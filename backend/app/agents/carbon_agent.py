"""碳汇分析 Agent"""
from app.agents.tools import register_tool
from app.services.carbon.carbon import CarbonService
from app.services.geo.postgis import PostGISSpatialService
from app.services.weather.weather_service import WeatherService


@register_tool("analyze_carbon")
async def analyze_carbon(db, field_id: str) -> dict:
    """分析地块碳汇变化并诊断原因"""
    carbon_svc = CarbonService(db)
    geo_svc = PostGISSpatialService(db)
    weather_svc = WeatherService()

    # 通过 Field 表获取 user_id，再查该用户的碳汇报告
    from sqlalchemy import select
    from app.models.field import Field
    field = (await db.execute(select(Field).where(Field.id == field_id))).scalar_one_or_none()
    if field:
        reports_total, reports = await carbon_svc.get_reports_by_user(str(field.user_id), 0, 100)
    else:
        reports_total, reports = 0, []
    field_reports = [r for r in reports if str(r.field_id) == field_id]

    if not field_reports:
        return {
            "field_id": field_id,
            "analysis": "该地块暂无碳汇报告，请先生成碳汇报告。",
        }

    latest = field_reports[0]
    field_info = await geo_svc.get_field_geom(field_id)
    centroid = field_info.get("centroid", [0, 0]) if field_info else [0, 0]
    weather = await weather_svc.get_current_weather(centroid[1], centroid[0])

    # 诊断分析
    factors = []
    if latest.carbon_amount and latest.carbon_amount < 1.0:
        factors.append("碳汇量偏低")
    if weather["precipitation_mm"] < 2:
        factors.append("近期降雨不足，影响秸秆腐解")
    if weather["humidity_pct"] < 50:
        factors.append("空气湿度偏低，腐解速率下降")

    from app.prompts import load_prompt
    analysis_template = load_prompt("carbon_analysis",
        field_name=field_info.get("name", "未知") if field_info else "未知",
        carbon_amount=latest.carbon_amount or 0,
        straw_amount=latest.straw_amount or 0,
        period_start=str(latest.period_start.date()) if latest.period_start else "",
        period_end=str(latest.period_end.date()) if latest.period_end else "",
        weather_summary=f"{weather['temperature_c']}°C, {weather['humidity_pct']}%, {weather['description']}",
        ndvi_trend="未知",
        organic_matter="未知",
    )

    return {
        "field_id": field_id,
        "field_name": field_info.get("name") if field_info else "未知",
        "latest_carbon_tco2e": latest.carbon_amount,
        "period": f"{latest.period_start.date()} ~ {latest.period_end.date()}",
        "weather_context": {
            "temperature_c": weather["temperature_c"],
            "precipitation_mm": weather["precipitation_mm"],
            "humidity_pct": weather["humidity_pct"],
        },
        "diagnosis": factors if factors else ["碳汇状况正常"],
        "recommendation": "建议增加灌溉" if "降雨不足" in str(factors) else "继续保持当前管理措施",
        "analysis_instructions": analysis_template,
    }