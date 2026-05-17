"""天气分析 Agent"""
from app.agents.tools import register_tool
from app.services.weather.weather_service import WeatherService
from app.services.geo.postgis import PostGISSpatialService


@register_tool("get_weather")
async def get_weather(db, field_id: str) -> dict:
    """获取地块天气信息"""
    geo_svc = PostGISSpatialService(db)
    weather_svc = WeatherService()

    field_info = await geo_svc.get_field_geom(field_id)
    if not field_info:
        return {"error": f"地块 {field_id} 不存在"}

    centroid = field_info["centroid"]
    lat, lon = centroid[1], centroid[0]
    current = await weather_svc.get_current_weather(lat, lon)
    forecast = await weather_svc.get_forecast(lat, lon, 5)
    agri = await weather_svc.get_agricultural_weather(lat, lon)

    from app.prompts import load_prompt
    forecast_summary = ", ".join(f"{d['date'][-5:]}: {d['temp_max']}/{d['temp_min']}°C, {d['description']}" for d in forecast[:5])
    analysis_template = load_prompt("weather_analysis",
        field_name=field_info["name"],
        temperature=current["temperature_c"],
        humidity=current["humidity_pct"],
        precipitation=current["precipitation_mm"],
        forecast=forecast_summary,
    )

    return {
        "field_id": field_id,
        "field_name": field_info["name"],
        "current": current,
        "forecast_5d": forecast,
        "agricultural_indicators": agri,
        "analysis_instructions": analysis_template,
    }


@register_tool("get_ndvi_trend")
async def get_ndvi_trend(db, field_id: str, days: int = 90) -> dict:
    """获取 NDVI 时序趋势"""
    from app.services.gee.gee_service import GEEService

    geo_svc = PostGISSpatialService(db)
    gee_svc = GEEService()

    field_info = await geo_svc.get_field_geom(field_id)
    centroid = field_info.get("centroid", [126.33, 45.39]) if field_info else [126.33, 45.39]
    ts_data = await gee_svc.get_ndvi_timeseries(field_id, centroid[0], centroid[1], days)

    values = [d["ndvi"] for d in ts_data if "ndvi" in d]
    trend = "上升" if len(values) >= 2 and values[-1] > values[0] else "下降" if len(values) >= 2 and values[-1] < values[0] else "稳定"

    return {
        "field_id": field_id,
        "field_name": field_info.get("name") if field_info else "未知",
        "ndvi_timeseries": ts_data,
        "mean_ndvi": round(sum(values) / len(values), 3) if values else None,
        "trend": trend,
        "days": days,
    }