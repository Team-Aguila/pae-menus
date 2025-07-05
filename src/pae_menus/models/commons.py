from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from beanie import PydanticObjectId
import re

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
    protein: Optional[float] = Field(default=None, description="Protein per serving (in grams)")
    carbohydrates: Optional[float] = Field(default=None, description="Carbohydrates per serving (in grams)")
    fat: Optional[float] = Field(default=None, description="Fat per serving (in grams)")
    fiber: Optional[float] = Field(default=None, description="Fiber per serving (in grams)")
    sodium: Optional[float] = Field(default=None, description="Sodium per serving (in mg)")
    calcium: Optional[float] = Field(default=None, description="Calcium per serving (in mg)")
    iron: Optional[float] = Field(default=None, description="Iron per serving (in mg)")
    vitamin_c: Optional[float] = Field(default=None, description="Vitamin C per serving (in mg)")
    vitamin_a: Optional[float] = Field(default=None, description="Vitamin A per serving (in IU)")
    photo_url: Optional[str] = Field(default=None, description="URL to a photo of the dish")
    
    @field_validator('protein', 'carbohydrates', 'fat', 'fiber', 'sodium', 'calcium', 'iron', 'vitamin_c', 'vitamin_a', mode='before')
    @classmethod
    def parse_numeric_value(cls, v):
        """Parse numeric values from strings like '25g', '100mg', etc."""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            # Extract numeric value from string like "25g", "100mg", "15.5g"
            match = re.search(r'(\d+\.?\d*)', v.strip())
            if match:
                return float(match.group(1))
            return None
        return v 