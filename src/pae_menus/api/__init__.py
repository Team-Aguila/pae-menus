# pae_menus/api/__init__.py 
from fastapi import APIRouter
from . import ingredients, dishes, menu_cycles, menu_schedules, nutritional_analysis

api_router = APIRouter()
api_router.include_router(ingredients.router, prefix="/ingredients", tags=["Ingredients"])
api_router.include_router(dishes.router, prefix="/dishes", tags=["Dishes"])
api_router.include_router(menu_cycles.router, prefix="/menu-cycles", tags=["Menu Cycles"])
api_router.include_router(menu_schedules.router, prefix="/menu-schedules", tags=["Menu Schedules"])
api_router.include_router(nutritional_analysis.router, prefix="/nutritional-analysis", tags=["Nutritional Analysis"]) 