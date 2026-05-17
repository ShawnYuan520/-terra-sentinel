"""天气 API — 带缓存"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.cache import weather_cache
from app.services.weather.weather_service import WeatherService

router = APIRouter(prefix="/weather", tags=["天气"])


@router.get("/current")
async def get_current_weather(
    lat: float = Query(...),
    lon: float = Query(...),
    current_user: dict = Depends(get_current_user),
):
    cache_key = f"current:{lat:.3f}:{lon:.3f}"
    cached = await weather_cache.get(cache_key)
    if cached is not None:
        return cached
    svc = WeatherService()
    result = await svc.get_current_weather(lat, lon)
    if result:
        await weather_cache.set(cache_key, result, ttl=600)  # 10分钟
    return result


@router.get("/forecast")
async def get_forecast(
    lat: float = Query(...),
    lon: float = Query(...),
    days: int = Query(5, ge=1, le=5),
    current_user: dict = Depends(get_current_user),
):
    cache_key = f"forecast:{lat:.3f}:{lon:.3f}:{days}"
    cached = await weather_cache.get(cache_key)
    if cached is not None:
        return cached
    svc = WeatherService()
    result = await svc.get_forecast(lat, lon, days)
    if result:
        await weather_cache.set(cache_key, result, ttl=1800)  # 30分钟
    return result


@router.get("/agricultural")
async def get_agricultural_weather(
    lat: float = Query(...),
    lon: float = Query(...),
    current_user: dict = Depends(get_current_user),
):
    cache_key = f"agri:{lat:.3f}:{lon:.3f}"
    cached = await weather_cache.get(cache_key)
    if cached is not None:
        return cached
    svc = WeatherService()
    result = await svc.get_agricultural_weather(lat, lon)
    if result:
        await weather_cache.set(cache_key, result, ttl=1800)  # 30分钟
    return result
