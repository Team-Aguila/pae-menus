from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional

from ..models.nutritional_analysis import (
    NutritionalAnalysisReport, SimplifiedNutritionalSummary, NutritionalComparisonReport
)
from ..services.nutritional_analysis_service import NutritionalAnalysisService

router = APIRouter(
    tags=["Nutritional Analysis"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/report/{schedule_id}",
    response_model=NutritionalAnalysisReport,
    summary="Generate comprehensive nutritional analysis report",
    description="Generate a complete nutritional analysis report for a menu schedule, including food groups, nutrients, and recommendations."
)
async def generate_nutritional_report(schedule_id: str) -> NutritionalAnalysisReport:
    """
    Generate a comprehensive nutritional analysis report for a menu schedule.
    
    This endpoint analyzes the nutritional content of a menu schedule and provides:
    - Daily nutritional analysis including food groups and nutrients
    - Average daily nutrient intake
    - Food group distribution and portions
    - Nutritional adequacy score
    - Recommendations for improvement
    
    Perfect for nutritionists to validate that menu schedules meet nutritional requirements.
    
    - **schedule_id**: The unique identifier of the menu schedule to analyze
    """
    return await NutritionalAnalysisService.generate_nutritional_report(schedule_id)


@router.get(
    "/summary/{schedule_id}",
    response_model=SimplifiedNutritionalSummary,
    summary="Get simplified nutritional summary",
    description="Get a simplified overview of nutritional content for quick assessment."
)
async def get_nutritional_summary(schedule_id: str) -> SimplifiedNutritionalSummary:
    """
    Get a simplified nutritional summary for quick overview.
    
    This endpoint provides a high-level summary including:
    - Total calories per day
    - Total protein per day
    - Food group distribution percentages
    - Overall nutritional balance score
    
    Ideal for quick assessments and dashboards.
    
    - **schedule_id**: The unique identifier of the menu schedule to analyze
    """
    return await NutritionalAnalysisService.get_simplified_summary(schedule_id)


@router.get(
    "/comparison/{schedule_id}",
    response_model=NutritionalComparisonReport,
    summary="Compare nutrition with standard requirements",
    description="Compare the nutritional content of a menu schedule against standard nutritional requirements."
)
async def compare_with_requirements(
    schedule_id: str,
    age_group: Optional[str] = Query(
        "school_age_6_12", 
        description="Age group for nutritional requirements (school_age_6_12 or school_age_13_18)"
    )
) -> NutritionalComparisonReport:
    """
    Compare menu nutrition with standard nutritional requirements.
    
    This endpoint compares the actual nutritional content of a menu schedule
    against established nutritional requirements for different age groups.
    
    Provides:
    - Compliance percentages for each nutrient
    - Overall compliance score and status
    - Areas needing improvement
    - Specific recommendations
    
    Essential for ensuring menu schedules meet nutritional standards.
    
    - **schedule_id**: The unique identifier of the menu schedule to analyze
    - **age_group**: Target age group (school_age_6_12 or school_age_13_18)
    """
    return await NutritionalAnalysisService.compare_with_requirements(schedule_id, age_group)


@router.get(
    "/food-groups/{schedule_id}",
    response_model=dict,
    summary="Get food group analysis",
    description="Get detailed food group analysis for a menu schedule."
)
async def get_food_group_analysis(schedule_id: str) -> dict:
    """
    Get detailed food group analysis for a menu schedule.
    
    This endpoint provides focused analysis on food group distribution:
    - Portions per food group
    - Dishes contributing to each group
    - Food group diversity metrics
    
    Useful for ensuring balanced food group representation.
    
    - **schedule_id**: The unique identifier of the menu schedule to analyze
    """
    try:
        full_report = await NutritionalAnalysisService.generate_nutritional_report(schedule_id)
        
        # Extract food group information
        food_group_analysis = {
            "menu_schedule_id": schedule_id,
            "menu_cycle_name": full_report.menu_cycle_name,
            "analysis_period": full_report.analysis_period,
            "average_daily_food_groups": [
                {
                    "food_group": fg.food_group.value,
                    "total_portions": fg.total_portions,
                    "dishes_count": fg.dishes_count,
                    "main_dishes": fg.main_dishes
                }
                for fg in full_report.average_daily_food_groups
            ],
            "food_group_diversity": len(full_report.average_daily_food_groups),
            "recommendations": [
                rec for rec in full_report.recommendations 
                if any(keyword in rec.lower() for keyword in ["group", "fruit", "vegetable", "dairy", "protein", "grain"])
            ]
        }
        
        return food_group_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating food group analysis: {str(e)}"
        )


@router.get(
    "/nutrients/{schedule_id}",
    response_model=dict,
    summary="Get nutrient analysis",
    description="Get detailed nutrient analysis for a menu schedule."
)
async def get_nutrient_analysis(schedule_id: str) -> dict:
    """
    Get detailed nutrient analysis for a menu schedule.
    
    This endpoint provides focused analysis on nutrient content:
    - Daily average nutrients
    - Key vitamin and mineral content
    - Macronutrient breakdown
    
    Essential for assessing nutritional adequacy.
    
    - **schedule_id**: The unique identifier of the menu schedule to analyze
    """
    try:
        full_report = await NutritionalAnalysisService.generate_nutritional_report(schedule_id)
        
        # Extract nutrient information
        nutrients = full_report.average_daily_nutrients
        
        nutrient_analysis = {
            "menu_schedule_id": schedule_id,
            "menu_cycle_name": full_report.menu_cycle_name,
            "analysis_period": full_report.analysis_period,
            "average_daily_nutrients": {
                "calories": nutrients.total_calories,
                "protein": nutrients.total_protein,
                "carbohydrates": nutrients.total_carbohydrates,
                "fat": nutrients.total_fat,
                "fiber": nutrients.total_fiber,
                "calcium": nutrients.total_calcium,
                "iron": nutrients.total_iron,
                "vitamin_c": nutrients.total_vitamin_c,
                "vitamin_a": nutrients.total_vitamin_a
            },
            "macronutrient_distribution": {
                "protein_percentage": (nutrients.total_protein * 4 / nutrients.total_calories * 100) if nutrients.total_calories > 0 else 0,
                "carbohydrate_percentage": (nutrients.total_carbohydrates * 4 / nutrients.total_calories * 100) if nutrients.total_calories > 0 else 0,
                "fat_percentage": (nutrients.total_fat * 9 / nutrients.total_calories * 100) if nutrients.total_calories > 0 else 0
            },
            "nutritional_adequacy_score": full_report.nutritional_adequacy_score,
            "recommendations": [
                rec for rec in full_report.recommendations 
                if any(keyword in rec.lower() for keyword in ["calorie", "protein", "vitamin", "mineral", "iron", "calcium"])
            ]
        }
        
        return nutrient_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating nutrient analysis: {str(e)}"
        ) 