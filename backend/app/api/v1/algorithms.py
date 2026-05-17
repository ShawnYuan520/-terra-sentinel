"""
算法服务 API
CUSUM物候 + AHP耕地评级 + 碳汇预测 + 农机路径
"""
import json
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.field import Field
from app.services.raster import RasterService
from app.services.phenology import detect_phenology, get_growth_stage_summary
from app.services.land_evaluation import evaluate_field
from app.services.carbon_model import predict_carbon_dynamics
from app.services.machinery_path import plan_field_path

router = APIRouter(prefix="/algorithms", tags=["算法服务"])


@router.get("/analysis/{field_id}")
async def full_field_analysis(
    field_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """田块全量算法分析 — 物候+评级+碳汇+路径, 一次返回"""

    # 1. 获取田块
    result = await db.execute(
        select(Field).where(Field.id == field_id, Field.user_id == current_user["sub"])
    )
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(404, "田块不存在")

    # 解析田块几何
    try:
        geom = json.loads(field.geom)
    except Exception:
        raise HTTPException(400, "田块几何数据无效")

    # 2. 提取中心坐标
    coords = geom.get("coordinates", [[[]]])[0]
    if not coords:
        raise HTTPException(400, "无法解析坐标")

    center_lon = sum(c[0] for c in coords) / len(coords)
    center_lat = sum(c[1] for c in coords) / len(coords)

    # 3. 土壤 + 栅格数据
    svc = RasterService()
    soil = svc.read_soil_profile(center_lon, center_lat)

    # NDVI 峰值估算 (从 SOC 和土地覆盖推导)
    lu = soil.get("landuse", 1)
    soc = soil.get("soc", 20)
    lu_ndvi_base = {1: 0.70, 2: 0.82, 3: 0.55, 4: 0.50, 5: 0.45}.get(int(lu), 0.65)
    ndvi_peak = min(0.92, lu_ndvi_base + (soc - 20) * 0.005)

    # 4. 耕地评级
    land_eval = evaluate_field(soil, ndvi_peak)

    # 5. 碳汇预测
    straw = field.area_ha * 150 * 15 / 100 if field.area_ha else 150  # 默认150kg/亩
    from app.services.weather.weather_service import WeatherService
    temp, moisture = 15, 60
    try:
        w = await WeatherService().get_current_weather(center_lat, center_lon)
        if w:
            temp = w.get("temperature_c", 15)
            moisture = w.get("humidity_pct", 60)
    except Exception:
        pass

    carbon = predict_carbon_dynamics(
        soc_current=soc,
        straw_input=straw,
        temperature_c=temp,
        moisture_pct=moisture,
        clay_pct=soil.get("clay") or 20,
        area_mu=(field.area_ha or 1) * 15,
        years=5,
    )

    # 6. 农机路径
    path = plan_field_path(geom, resolution=15)

    return {
        "field_id": field_id,
        "field_name": field.name,
        "center": {"lon": round(center_lon, 5), "lat": round(center_lat, 5)},
        "soil_profile": soil,
        "land_evaluation": land_eval,
        "carbon_prediction": carbon,
        "machinery_path": {
            "total_distance_m": path.get("total_distance_m", 0),
            "avg_slope": path.get("avg_slope", 0),
            "steep_zones": path.get("steep_zones", []),
            "recommendation": path.get("recommendation", ""),
        },
        "generated_at": __import__("datetime").datetime.now().isoformat(),
    }


@router.get("/phenology/{field_id}")
async def get_phenology(
    field_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """CUSUM物候检测 — 从NDVI时序识别生长阶段"""
    result = await db.execute(
        select(Field).where(Field.id == field_id, Field.user_id == current_user["sub"])
    )
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(404, "田块不存在")

    # 从GEE获取NDVI时序 (或栅格推导)
    try:
        from app.services.gee.gee_service import GEEService
        geom = json.loads(field.geom)
        coords = geom["coordinates"][0]
        lon = sum(c[0] for c in coords) / len(coords)
        lat = sum(c[1] for c in coords) / len(coords)
        gee = GEEService()
        ndvi_data = await gee.get_ndvi_timeseries(field_id, lon, lat, days=365)
    except Exception:
        ndvi_data = []

    phenology = detect_phenology(ndvi_data)
    current_ndvi = ndvi_data[-1]["ndvi"] if ndvi_data else 0
    summary = get_growth_stage_summary(phenology, current_ndvi)

    return {
        "field_id": field_id,
        "phenology": phenology,
        "current_ndvi": current_ndvi,
        "summary": summary,
    }


@router.post("/carbon-model")
async def run_carbon_model(data: dict, current_user: dict = Depends(get_current_user)):
    """碳汇预测模型"""
    required = ["soc_current", "straw_input", "temperature_c", "moisture_pct"]
    for k in required:
        if k not in data:
            raise HTTPException(400, f"缺少参数: {k}")

    return predict_carbon_dynamics(
        soc_current=data["soc_current"],
        straw_input=data["straw_input"],
        temperature_c=data["temperature_c"],
        moisture_pct=data["moisture_pct"],
        clay_pct=data.get("clay_pct", 20),
        area_mu=data.get("area_mu", 100),
        years=data.get("years", 5),
    )
