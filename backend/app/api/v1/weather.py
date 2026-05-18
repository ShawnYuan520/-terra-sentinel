"""天气 API"""
from fastapi import APIRouter, Depends, Query
from app.core.deps import get_optional_user
from app.services.weather.weather_service import WeatherService

router = APIRouter(prefix="/weather", tags=["天气"])


@router.get("/current")
async def get_current_weather(
    lat: float = Query(...),
    lon: float = Query(...),
    current_user: dict | None = Depends(get_optional_user),
):
    return await WeatherService().get_current_weather(lat, lon)


@router.get("/forecast")
async def get_forecast(
    lat: float = Query(...),
    lon: float = Query(...),
    days: int = Query(5, ge=1, le=5),
    current_user: dict | None = Depends(get_optional_user),
):
    return await WeatherService().get_forecast(lat, lon, days)


@router.get("/agricultural")
async def get_agricultural_weather(
    lat: float = Query(...),
    lon: float = Query(...),
    current_user: dict | None = Depends(get_optional_user),
):
    return await WeatherService().get_agricultural_weather(lat, lon)
