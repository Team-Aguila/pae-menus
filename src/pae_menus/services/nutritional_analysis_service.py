from typing import List, Dict, Optional
from datetime import date as Date, timedelta
from beanie import PydanticObjectId
from fastapi import HTTPException, status

from ..models.nutritional_analysis import (
    FoodGroup, FoodGroupPortion, NutrientSummary, DailyNutritionalAnalysis,
    NutritionalAnalysisReport, SimplifiedNutritionalSummary,
    NutritionalRequirements, NutritionalComparisonReport
)
from ..models.menu_schedule import MenuSchedule, MenuScheduleStatus
from ..models.menu_cycle import MenuCycle
from ..models.dish import Dish, DishType
from ..models.ingredient import Ingredient


class NutritionalAnalysisService:
    """Service for generating nutritional analysis reports from menu schedules"""
    
    # Mapping from dish types to food groups
    DISH_TYPE_TO_FOOD_GROUP = {
        DishType.CEREAL: FoodGroup.GRAINS,
        DishType.PROTEIN: FoodGroup.PROTEIN,
        DishType.VEGETABLE: FoodGroup.VEGETABLES,
        DishType.FRUIT: FoodGroup.FRUITS,
        DishType.DAIRY: FoodGroup.DAIRY,
        DishType.OTHER: FoodGroup.GRAINS  # Default fallback
    }
    
    # Mapping from ingredient categories to food groups
    INGREDIENT_CATEGORY_TO_FOOD_GROUP = {
        "cereales": FoodGroup.GRAINS,
        "legumbres": FoodGroup.LEGUMES,
        "proteinas": FoodGroup.PROTEIN,
        "verduras": FoodGroup.VEGETABLES,
        "frutas": FoodGroup.FRUITS,
        "lacteos": FoodGroup.DAIRY,
        "tuberculos": FoodGroup.GRAINS,  # Potatoes, yuca, etc. as carb source
        "aceites": FoodGroup.PROTEIN,  # Fats grouped with protein
        "condimentos": FoodGroup.VEGETABLES,  # Herbs and spices
    }
    
    @staticmethod
    async def generate_nutritional_report(schedule_id: str) -> NutritionalAnalysisReport:
        """
        Generate a complete nutritional analysis report for a menu schedule
        
        Args:
            schedule_id: ID of the menu schedule to analyze
            
        Returns:
            NutritionalAnalysisReport: Complete nutritional analysis
            
        Raises:
            HTTPException: If schedule not found or analysis fails
        """
        try:
            # Get the menu schedule
            schedule = await MenuSchedule.get(PydanticObjectId(schedule_id))
            if not schedule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Menu schedule with id '{schedule_id}' not found"
                )
            
            # Get the menu cycle
            menu_cycle = await MenuCycle.get(schedule.menu_cycle_id)
            if not menu_cycle:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Menu cycle with id '{schedule.menu_cycle_id}' not found"
                )
            
            # Generate date range for the schedule
            schedule_dates = []
            current_date = schedule.start_date
            while current_date <= schedule.end_date:
                schedule_dates.append(current_date)
                current_date += timedelta(days=1)
            
            # Analyze each day
            daily_analyses = []
            for schedule_date in schedule_dates:
                days_since_start = (schedule_date - schedule.start_date).days
                cycle_day = (days_since_start % menu_cycle.duration_days) + 1
                
                daily_analysis = await NutritionalAnalysisService._analyze_daily_menu(
                    menu_cycle, cycle_day, schedule_date
                )
                daily_analyses.append(daily_analysis)
            
            # Calculate average nutrients and food groups
            avg_nutrients = NutritionalAnalysisService._calculate_average_nutrients(daily_analyses)
            avg_food_groups = NutritionalAnalysisService._calculate_average_food_groups(daily_analyses)
            
            # Calculate nutritional adequacy score
            adequacy_score = NutritionalAnalysisService._calculate_adequacy_score(avg_nutrients, avg_food_groups)
            
            # Generate recommendations
            recommendations = NutritionalAnalysisService._generate_recommendations(avg_nutrients, avg_food_groups)
            
            return NutritionalAnalysisReport(
                menu_schedule_id=schedule_id,
                menu_cycle_name=menu_cycle.name,
                analysis_period={
                    "start_date": schedule.start_date.isoformat(),
                    "end_date": schedule.end_date.isoformat()
                },
                location_count=len(schedule.coverage),
                total_days=len(schedule_dates),
                daily_analysis=daily_analyses,
                average_daily_nutrients=avg_nutrients,
                average_daily_food_groups=avg_food_groups,
                nutritional_adequacy_score=adequacy_score,
                recommendations=recommendations
            )
            
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid menu schedule ID format"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating nutritional report: {str(e)}"
            )
    
    @staticmethod
    async def _analyze_daily_menu(menu_cycle: MenuCycle, cycle_day: int, analysis_date: Date) -> DailyNutritionalAnalysis:
        """Analyze nutritional content for a specific day"""
        
        # Find the daily menu for this cycle day
        daily_menu = None
        for dm in menu_cycle.daily_menus:
            if dm.day == cycle_day:
                daily_menu = dm
                break
        
        if not daily_menu:
            return DailyNutritionalAnalysis(
                date=analysis_date,
                cycle_day=cycle_day,
                food_groups=[],
                nutrients=NutrientSummary(),
                total_dishes=0
            )
        
        # Collect all dish IDs for the day
        all_dish_ids = []
        all_dish_ids.extend(daily_menu.breakfast_dish_ids)
        all_dish_ids.extend(daily_menu.lunch_dish_ids)
        all_dish_ids.extend(daily_menu.snack_dish_ids)
        
        if not all_dish_ids:
            return DailyNutritionalAnalysis(
                date=analysis_date,
                cycle_day=cycle_day,
                food_groups=[],
                nutrients=NutrientSummary(),
                total_dishes=0
            )
        
        # Get dish details
        dishes = await Dish.find({"_id": {"$in": all_dish_ids}}).to_list()
        
        # Analyze food groups
        food_group_analysis = await NutritionalAnalysisService._analyze_food_groups(dishes)
        
        # Calculate nutrients
        nutrient_summary = NutritionalAnalysisService._calculate_daily_nutrients(dishes)
        
        return DailyNutritionalAnalysis(
            date=analysis_date,
            cycle_day=cycle_day,
            food_groups=food_group_analysis,
            nutrients=nutrient_summary,
            total_dishes=len(dishes)
        )
    
    @staticmethod
    async def _analyze_food_groups(dishes: List[Dish]) -> List[FoodGroupPortion]:
        """Analyze food groups from a list of dishes"""
        
        food_group_data = {}
        
        for dish in dishes:
            # Determine food group from dish type
            food_group = None
            if dish.dish_type:
                food_group = NutritionalAnalysisService.DISH_TYPE_TO_FOOD_GROUP.get(dish.dish_type)
            
            # If no dish type, try to determine from ingredients
            if not food_group and dish.recipe and dish.recipe.ingredients:
                food_group = await NutritionalAnalysisService._determine_food_group_from_ingredients(
                    dish.recipe.ingredients
                )
            
            # Default to grains if can't determine
            if not food_group:
                food_group = FoodGroup.GRAINS
            
            # Initialize food group data if not exists
            if food_group not in food_group_data:
                food_group_data[food_group] = {
                    "total_portions": 0.0,
                    "dishes_count": 0,
                    "main_dishes": []
                }
            
            # Add dish to food group (assuming 1 portion per dish)
            food_group_data[food_group]["total_portions"] += 1.0
            food_group_data[food_group]["dishes_count"] += 1
            food_group_data[food_group]["main_dishes"].append(dish.name)
        
        # Convert to FoodGroupPortion objects
        food_group_portions = []
        for food_group, data in food_group_data.items():
            food_group_portions.append(FoodGroupPortion(
                food_group=food_group,
                total_portions=data["total_portions"],
                dishes_count=data["dishes_count"],
                main_dishes=data["main_dishes"]
            ))
        
        return food_group_portions
    
    @staticmethod
    async def _determine_food_group_from_ingredients(ingredients) -> Optional[FoodGroup]:
        """Determine food group from dish ingredients"""
        
        # Get ingredient IDs
        ingredient_ids = [ingredient.ingredient_id for ingredient in ingredients]
        
        # Get ingredient details
        ingredient_docs = await Ingredient.find({"_id": {"$in": ingredient_ids}}).to_list()
        
        # Count categories
        category_weights = {}
        for ingredient in ingredient_docs:
            if ingredient.category:
                food_group = NutritionalAnalysisService.INGREDIENT_CATEGORY_TO_FOOD_GROUP.get(
                    ingredient.category.lower()
                )
                if food_group:
                    category_weights[food_group] = category_weights.get(food_group, 0) + 1
        
        # Return the most common food group
        if category_weights:
            return max(category_weights, key=category_weights.get)
        
        return None
    
    @staticmethod
    def _calculate_daily_nutrients(dishes: List[Dish]) -> NutrientSummary:
        """Calculate total nutrients for a list of dishes"""
        
        total_nutrients = NutrientSummary()
        
        for dish in dishes:
            if dish.nutritional_info:
                ni = dish.nutritional_info
                total_nutrients.total_calories += ni.calories or 0.0
                total_nutrients.total_protein += ni.protein or 0.0
                total_nutrients.total_carbohydrates += ni.carbohydrates or 0.0
                total_nutrients.total_fat += ni.fat or 0.0
                total_nutrients.total_fiber += ni.fiber or 0.0
                total_nutrients.total_calcium += ni.calcium or 0.0
                total_nutrients.total_iron += ni.iron or 0.0
                total_nutrients.total_vitamin_c += ni.vitamin_c or 0.0
                total_nutrients.total_vitamin_a += ni.vitamin_a or 0.0
        
        return total_nutrients
    
    @staticmethod
    def _calculate_average_nutrients(daily_analyses: List[DailyNutritionalAnalysis]) -> NutrientSummary:
        """Calculate average daily nutrients across all days"""
        
        if not daily_analyses:
            return NutrientSummary()
        
        total_nutrients = NutrientSummary()
        
        for analysis in daily_analyses:
            nutrients = analysis.nutrients
            total_nutrients.total_calories += nutrients.total_calories
            total_nutrients.total_protein += nutrients.total_protein
            total_nutrients.total_carbohydrates += nutrients.total_carbohydrates
            total_nutrients.total_fat += nutrients.total_fat
            total_nutrients.total_fiber += nutrients.total_fiber
            total_nutrients.total_calcium += nutrients.total_calcium
            total_nutrients.total_iron += nutrients.total_iron
            total_nutrients.total_vitamin_c += nutrients.total_vitamin_c
            total_nutrients.total_vitamin_a += nutrients.total_vitamin_a
        
        # Calculate averages
        days_count = len(daily_analyses)
        return NutrientSummary(
            total_calories=total_nutrients.total_calories / days_count,
            total_protein=total_nutrients.total_protein / days_count,
            total_carbohydrates=total_nutrients.total_carbohydrates / days_count,
            total_fat=total_nutrients.total_fat / days_count,
            total_fiber=total_nutrients.total_fiber / days_count,
            total_calcium=total_nutrients.total_calcium / days_count,
            total_iron=total_nutrients.total_iron / days_count,
            total_vitamin_c=total_nutrients.total_vitamin_c / days_count,
            total_vitamin_a=total_nutrients.total_vitamin_a / days_count
        )
    
    @staticmethod
    def _calculate_average_food_groups(daily_analyses: List[DailyNutritionalAnalysis]) -> List[FoodGroupPortion]:
        """Calculate average food group portions across all days"""
        
        if not daily_analyses:
            return []
        
        food_group_totals = {}
        
        for analysis in daily_analyses:
            for food_group_portion in analysis.food_groups:
                food_group = food_group_portion.food_group
                
                if food_group not in food_group_totals:
                    food_group_totals[food_group] = {
                        "total_portions": 0.0,
                        "dishes_count": 0,
                        "main_dishes": set()
                    }
                
                food_group_totals[food_group]["total_portions"] += food_group_portion.total_portions
                food_group_totals[food_group]["dishes_count"] += food_group_portion.dishes_count
                food_group_totals[food_group]["main_dishes"].update(food_group_portion.main_dishes)
        
        # Calculate averages
        days_count = len(daily_analyses)
        average_food_groups = []
        
        for food_group, data in food_group_totals.items():
            average_food_groups.append(FoodGroupPortion(
                food_group=food_group,
                total_portions=data["total_portions"] / days_count,
                dishes_count=int(data["dishes_count"] / days_count),
                main_dishes=list(data["main_dishes"])[:5]  # Top 5 dishes
            ))
        
        return average_food_groups
    
    @staticmethod
    def _calculate_adequacy_score(nutrients: NutrientSummary, food_groups: List[FoodGroupPortion]) -> float:
        """Calculate nutritional adequacy score (0-100)"""
        
        score = 0.0
        
        # Nutrient score (50% of total)
        nutrient_score = 0.0
        if nutrients.total_calories > 1500:  # School-age children need ~1800-2000 calories
            nutrient_score += 15
        if nutrients.total_protein > 40:  # School-age children need ~45-50g protein
            nutrient_score += 15
        if nutrients.total_calcium > 800:  # School-age children need ~1000mg calcium
            nutrient_score += 10
        if nutrients.total_iron > 8:  # School-age children need ~10mg iron
            nutrient_score += 10
        
        # Food group diversity score (50% of total)
        food_group_score = 0.0
        food_group_names = [fg.food_group for fg in food_groups]
        
        # Points for each food group present
        if FoodGroup.GRAINS in food_group_names:
            food_group_score += 10
        if FoodGroup.PROTEIN in food_group_names:
            food_group_score += 10
        if FoodGroup.VEGETABLES in food_group_names:
            food_group_score += 10
        if FoodGroup.FRUITS in food_group_names:
            food_group_score += 10
        if FoodGroup.DAIRY in food_group_names:
            food_group_score += 5
        if FoodGroup.LEGUMES in food_group_names:
            food_group_score += 5
        
        score = nutrient_score + food_group_score
        return min(score, 100.0)  # Cap at 100
    
    @staticmethod
    def _generate_recommendations(nutrients: NutrientSummary, food_groups: List[FoodGroupPortion]) -> List[str]:
        """Generate nutritional recommendations"""
        
        recommendations = []
        
        # Check nutrient adequacy
        if nutrients.total_calories < 1500:
            recommendations.append("Consider increasing portion sizes or adding more calorie-dense foods to meet energy needs")
        
        if nutrients.total_protein < 40:
            recommendations.append("Include more protein-rich foods such as legumes, dairy, eggs, or meat")
        
        if nutrients.total_calcium < 800:
            recommendations.append("Add more dairy products or calcium-rich foods like cheese, yogurt, or fortified foods")
        
        if nutrients.total_iron < 8:
            recommendations.append("Include iron-rich foods such as red meat, beans, or fortified cereals")
        
        if nutrients.total_fiber < 20:
            recommendations.append("Increase fiber intake with more fruits, vegetables, and whole grains")
        
        # Check food group diversity
        food_group_names = [fg.food_group for fg in food_groups]
        
        if FoodGroup.FRUITS not in food_group_names:
            recommendations.append("Add fresh fruits to provide vitamins, minerals, and fiber")
        
        if FoodGroup.VEGETABLES not in food_group_names:
            recommendations.append("Include more vegetables for essential vitamins and minerals")
        
        if FoodGroup.LEGUMES not in food_group_names:
            recommendations.append("Consider adding legumes (beans, lentils) for protein and fiber")
        
        if FoodGroup.DAIRY not in food_group_names:
            recommendations.append("Include dairy products for calcium and protein")
        
        # General recommendations
        if len(food_groups) < 4:
            recommendations.append("Increase food group diversity to ensure balanced nutrition")
        
        if not recommendations:
            recommendations.append("The menu shows good nutritional balance. Continue with current planning")
        
        return recommendations
    
    @staticmethod
    async def get_simplified_summary(schedule_id: str) -> SimplifiedNutritionalSummary:
        """Get simplified nutritional summary for quick overview"""
        
        full_report = await NutritionalAnalysisService.generate_nutritional_report(schedule_id)
        
        # Calculate food group distribution
        food_group_distribution = {}
        total_portions = sum(fg.total_portions for fg in full_report.average_daily_food_groups)
        
        for fg in full_report.average_daily_food_groups:
            if total_portions > 0:
                food_group_distribution[fg.food_group.value] = (fg.total_portions / total_portions) * 100
        
        return SimplifiedNutritionalSummary(
            total_calories_per_day=full_report.average_daily_nutrients.total_calories,
            total_protein_per_day=full_report.average_daily_nutrients.total_protein,
            food_group_distribution=food_group_distribution,
            nutritional_balance_score=full_report.nutritional_adequacy_score
        )
    
    @staticmethod
    async def compare_with_requirements(schedule_id: str, age_group: str = "school_age_6_12") -> NutritionalComparisonReport:
        """Compare menu nutrition with standard requirements"""
        
        # Define nutritional requirements for different age groups
        requirements_data = {
            "school_age_6_12": NutritionalRequirements(
                age_group="school_age_6_12",
                daily_calories=1800.0,
                daily_protein=45.0,
                daily_calcium=1000.0,
                daily_iron=10.0,
                daily_vitamin_c=45.0,
                daily_vitamin_a=700.0
            ),
            "school_age_13_18": NutritionalRequirements(
                age_group="school_age_13_18",
                daily_calories=2200.0,
                daily_protein=55.0,
                daily_calcium=1200.0,
                daily_iron=12.0,
                daily_vitamin_c=75.0,
                daily_vitamin_a=900.0
            )
        }
        
        requirements = requirements_data.get(age_group, requirements_data["school_age_6_12"])
        
        # Get actual intake
        full_report = await NutritionalAnalysisService.generate_nutritional_report(schedule_id)
        actual_intake = full_report.average_daily_nutrients
        
        # Calculate compliance percentages
        calorie_compliance = (actual_intake.total_calories / requirements.daily_calories) * 100
        protein_compliance = (actual_intake.total_protein / requirements.daily_protein) * 100
        calcium_compliance = (actual_intake.total_calcium / requirements.daily_calcium) * 100
        iron_compliance = (actual_intake.total_iron / requirements.daily_iron) * 100
        vitamin_c_compliance = (actual_intake.total_vitamin_c / requirements.daily_vitamin_c) * 100
        vitamin_a_compliance = (actual_intake.total_vitamin_a / requirements.daily_vitamin_a) * 100
        
        # Calculate overall compliance
        overall_compliance = (
            calorie_compliance + protein_compliance + calcium_compliance +
            iron_compliance + vitamin_c_compliance + vitamin_a_compliance
        ) / 6
        
        # Determine compliance status
        if overall_compliance >= 90:
            compliance_status = "excellent"
        elif overall_compliance >= 80:
            compliance_status = "good"
        elif overall_compliance >= 70:
            compliance_status = "fair"
        else:
            compliance_status = "poor"
        
        # Generate improvement areas
        improvement_areas = []
        if calorie_compliance < 80:
            improvement_areas.append("Energy/Calories")
        if protein_compliance < 80:
            improvement_areas.append("Protein")
        if calcium_compliance < 80:
            improvement_areas.append("Calcium")
        if iron_compliance < 80:
            improvement_areas.append("Iron")
        if vitamin_c_compliance < 80:
            improvement_areas.append("Vitamin C")
        if vitamin_a_compliance < 80:
            improvement_areas.append("Vitamin A")
        
        return NutritionalComparisonReport(
            menu_schedule_id=schedule_id,
            requirements=requirements,
            actual_intake=actual_intake,
            calorie_compliance=calorie_compliance,
            protein_compliance=protein_compliance,
            calcium_compliance=calcium_compliance,
            iron_compliance=iron_compliance,
            vitamin_c_compliance=vitamin_c_compliance,
            vitamin_a_compliance=vitamin_a_compliance,
            overall_compliance=overall_compliance,
            compliance_status=compliance_status,
            improvement_areas=improvement_areas,
            recommendations=full_report.recommendations
        ) 