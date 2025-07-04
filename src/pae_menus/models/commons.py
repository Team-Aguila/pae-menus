from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional
from beanie import PydanticObjectId

class MealType(str, Enum):
    """
    Meal types for dish categorization.
    
    Values:
    - desayuno: Breakfast meal
    - almuerzo: Lunch meal  
    - refrigerio: Snack meal
    """
    BREAKFAST = "desayuno"
    LUNCH = "almuerzo"
    SNACK = "refrigerio"

class Portion(BaseModel):
    ingredient_id: PydanticObjectId
    quantity: float = Field(..., gt=0, description="Net quantity of the ingredient")
    unit: str = Field(..., min_length=1, description="Unit of measure for the quantity")

class Recipe(BaseModel):
    ingredients: List[Portion] = Field(default=[], description="List of ingredients and their portions")

class DailyMenu(BaseModel):
    day: int = Field(..., ge=1, description="Day of the cycle")
    breakfast_dish_ids: List[PydanticObjectId] = Field(default=[])
    lunch_dish_ids: List[PydanticObjectId] = Field(default=[])
    snack_dish_ids: List[PydanticObjectId] = Field(default=[])

class NutritionalInfo(BaseModel):
    calories: Optional[float] = Field(default=None, description="Calories per serving")
    protein: Optional[str] = Field(default=None, description="Protein per serving (e.g., '45g')")
    photo_url: Optional[str] = Field(default=None, description="URL to a photo of the dish") 