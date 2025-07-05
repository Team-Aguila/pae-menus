from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import date as Date
from enum import Enum


class FoodGroup(str, Enum):
    """
    Food group categories for nutritional analysis.
    
    Values:
    - grains: Grains and cereals (rice, pasta, bread, oats, etc.)
    - legumes: Legumes and beans (lentils, chickpeas, black beans, etc.)
    - dairy: Dairy products (milk, cheese, yogurt, etc.)
    - fruits: Fruits and fruit-based dishes
    - vegetables: Vegetables and vegetable-based dishes
    - protein: Protein sources (meat, fish, eggs, nuts, etc.)
    """
    GRAINS = "grains"
    LEGUMES = "legumes"
    DAIRY = "dairy"
    FRUITS = "fruits"
    VEGETABLES = "vegetables"
    PROTEIN = "protein"


class FoodGroupPortion(BaseModel):
    """Individual food group portion information"""
    food_group: FoodGroup = Field(..., description="Food group category")
    total_portions: float = Field(..., description="Total portions for this food group")
    dishes_count: int = Field(..., description="Number of dishes contributing to this food group")
    main_dishes: List[str] = Field(..., description="Names of main dishes in this food group")


class NutrientSummary(BaseModel):
    """Summary of key nutrients"""
    total_calories: float = Field(0.0, description="Total calories per person per day")
    total_protein: float = Field(0.0, description="Total protein in grams per person per day")
    total_carbohydrates: float = Field(0.0, description="Total carbohydrates in grams per person per day")
    total_fat: float = Field(0.0, description="Total fat in grams per person per day")
    total_fiber: float = Field(0.0, description="Total fiber in grams per person per day")
    total_calcium: float = Field(0.0, description="Total calcium in mg per person per day")
    total_iron: float = Field(0.0, description="Total iron in mg per person per day")
    total_vitamin_c: float = Field(0.0, description="Total vitamin C in mg per person per day")
    total_vitamin_a: float = Field(0.0, description="Total vitamin A in IU per person per day")


class DailyNutritionalAnalysis(BaseModel):
    """Nutritional analysis for a specific day"""
    date: Date = Field(..., description="Date of the analysis")
    cycle_day: int = Field(..., description="Day in the menu cycle")
    food_groups: List[FoodGroupPortion] = Field(..., description="Food group analysis")
    nutrients: NutrientSummary = Field(..., description="Nutrient summary")
    total_dishes: int = Field(..., description="Total number of dishes for this day")


class NutritionalAnalysisReport(BaseModel):
    """Complete nutritional analysis report for a menu schedule"""
    menu_schedule_id: str = Field(..., description="ID of the menu schedule")
    menu_cycle_name: str = Field(..., description="Name of the menu cycle")
    analysis_period: dict = Field(..., description="Analysis period with start and end dates")
    location_count: int = Field(..., description="Number of locations covered")
    total_days: int = Field(..., description="Total number of days in the analysis")
    
    # Daily analysis
    daily_analysis: List[DailyNutritionalAnalysis] = Field(..., description="Daily nutritional analysis")
    
    # Summary statistics
    average_daily_nutrients: NutrientSummary = Field(..., description="Average daily nutrient intake")
    average_daily_food_groups: List[FoodGroupPortion] = Field(..., description="Average daily food group portions")
    
    # Compliance and recommendations
    nutritional_adequacy_score: float = Field(..., description="Overall nutritional adequacy score (0-100)")
    recommendations: List[str] = Field(..., description="Nutritional recommendations")


class SimplifiedNutritionalSummary(BaseModel):
    """Simplified nutritional summary for quick overview"""
    total_calories_per_day: float = Field(..., description="Average calories per person per day")
    total_protein_per_day: float = Field(..., description="Average protein per person per day")
    food_group_distribution: Dict[str, float] = Field(..., description="Food group distribution percentages")
    nutritional_balance_score: float = Field(..., description="Nutritional balance score (0-100)")
    
    
class NutritionalRequirements(BaseModel):
    """Nutritional requirements for comparison"""
    age_group: str = Field(..., description="Age group (e.g., 'school_age_6_12')")
    daily_calories: float = Field(..., description="Required daily calories")
    daily_protein: float = Field(..., description="Required daily protein in grams")
    daily_calcium: float = Field(..., description="Required daily calcium in mg")
    daily_iron: float = Field(..., description="Required daily iron in mg")
    daily_vitamin_c: float = Field(..., description="Required daily vitamin C in mg")
    daily_vitamin_a: float = Field(..., description="Required daily vitamin A in IU")
    
    
class NutritionalComparisonReport(BaseModel):
    """Comparison report between actual intake and requirements"""
    menu_schedule_id: str = Field(..., description="ID of the menu schedule")
    requirements: NutritionalRequirements = Field(..., description="Nutritional requirements")
    actual_intake: NutrientSummary = Field(..., description="Actual average daily intake")
    
    # Compliance percentages
    calorie_compliance: float = Field(..., description="Calorie compliance percentage")
    protein_compliance: float = Field(..., description="Protein compliance percentage")
    calcium_compliance: float = Field(..., description="Calcium compliance percentage")
    iron_compliance: float = Field(..., description="Iron compliance percentage")
    vitamin_c_compliance: float = Field(..., description="Vitamin C compliance percentage")
    vitamin_a_compliance: float = Field(..., description="Vitamin A compliance percentage")
    
    # Overall compliance
    overall_compliance: float = Field(..., description="Overall compliance percentage")
    compliance_status: str = Field(..., description="Compliance status (excellent/good/fair/poor)")
    
    # Recommendations
    improvement_areas: List[str] = Field(..., description="Areas needing improvement")
    recommendations: List[str] = Field(..., description="Specific recommendations") 