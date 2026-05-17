from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.fields import router as fields_router
from app.api.v1.soil import router as soil_router
from app.api.v1.carbon import router as carbon_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.agent import router as agent_router
from app.api.v1.geo import router as geo_router
from app.api.v1.weather import router as weather_router
from app.api.v1.raster import router as raster_router
from app.api.v1.algorithms import router as algo_router
from app.api.v1.products import router as products_router
from app.api.v1.platform import router as platform_router
from app.api.v1.help import router as help_router
from app.api.v1.settings import router as settings_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(fields_router)
api_router.include_router(soil_router)
api_router.include_router(carbon_router)
api_router.include_router(knowledge_router)
api_router.include_router(agent_router)
api_router.include_router(geo_router)
api_router.include_router(weather_router)
api_router.include_router(raster_router)
api_router.include_router(algo_router)
api_router.include_router(products_router)
api_router.include_router(platform_router)
api_router.include_router(help_router)
api_router.include_router(settings_router)
