import asyncio
from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user
from app.core.cache import raster_cache, weather_cache, cached
from app.services.raster import RasterService, RASTER_CONFIG
from app.schemas.raster import RasterPointOut, RasterStatsOut, SoilProfileOut

router = APIRouter(prefix="/raster", tags=["raster"])


@router.get("/list")
async def list_rasters(current_user: dict | None = Depends(get_optional_user)):
    svc = RasterService()
    result = {}
    for name, cfg in RASTER_CONFIG.items():
        # 先尝试从数据库读取元数据，没有则从文件读取并写入数据库
        stats = svc.read_stats_from_db(name)
        if not stats:
            stats = svc.read_stats(name)
            if stats:
                svc.save_stats_to_db(name, stats)
        if stats:
            stats["name"] = name
            stats["description"] = cfg["desc"]
            result[name] = stats
    return result


@router.get("/{name}/point", response_model=RasterPointOut)
async def raster_point(
    name: str,
    lon: float = Query(...),
    lat: float = Query(...),
    current_user: dict | None = Depends(get_optional_user),
):
    if name not in RASTER_CONFIG:
        raise HTTPException(404, f"Raster layer '{name}' not found")
    svc = RasterService()
    val = await svc.read_at_point_async(name, lon, lat)
    return RasterPointOut(raster=name, lon=lon, lat=lat, value=val)


@router.get("/{name}/tile/{z}/{x}/{y}")
async def raster_tile(
    name: str, z: int, x: int, y: int,
    colormap: str = "viridis",
):
    """PNG tile for Leaflet overlay. No auth — loaded via <img> tags."""
    if name not in RASTER_CONFIG:
        raise HTTPException(404, f"Raster layer '{name}' not found")
    # 瓦片缓存 (静态数据，长TTL)
    tile_key = f"tile:{name}:{z}:{x}:{y}:{colormap}"
    cached_tile = await raster_cache.get(tile_key)
    if cached_tile is not None:
        return Response(content=cached_tile, media_type="image/png")
    svc = RasterService()
    png = svc.generate_tile(name, z, x, y, colormap)
    if png:
        await raster_cache.set(tile_key, png, ttl=86400 * 30)
    return Response(content=png, media_type="image/png")


@router.get("/soil-profile", response_model=SoilProfileOut)
async def soil_profile(
    lon: float = Query(...),
    lat: float = Query(...),
    current_user: dict | None = Depends(get_optional_user),
):
    # 缓存栅格数据（土壤剖面是静态的，365天TTL）
    cache_key = f"soil:{lon:.4f}:{lat:.4f}"
    cached_val = await raster_cache.get(cache_key)
    if cached_val is not None:
        return cached_val
    svc = RasterService()
    result = await svc.read_soil_profile_async(lon, lat)
    if result:
        await raster_cache.set(cache_key, result, ttl=86400 * 365)
    return result


@router.get("/decision")
async def agricultural_decision(
    lon: float = Query(...),
    lat: float = Query(...),
    crop: str = Query("玉米"),
    area_mu: float = Query(100),
    db: AsyncSession = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user),
):
    """农业决策闭环：诊断→处方→预测"""
    svc = RasterService()
    soil = await svc.read_soil_profile_async(lon, lat)

    # ── 诊断 ──
    diagnoses = []
    if soil.get("soc") is not None:
        soc = soil["soc"]
        if soc > 25: diagnoses.append({"level": "good", "msg": f"有机碳含量高 ({soc:.1f} g/kg)，土壤肥力优良"})
        elif soc > 15: diagnoses.append({"level": "ok", "msg": f"有机碳含量中等 ({soc:.1f} g/kg)，建议增施有机肥"})
        else: diagnoses.append({"level": "warn", "msg": f"有机碳偏低 ({soc:.1f} g/kg)，需秸秆还田提升"})
    if soil.get("ph") is not None:
        ph = soil["ph"]
        if 6.0 <= ph <= 7.5: diagnoses.append({"level": "good", "msg": f"pH {ph} 适宜作物生长"})
        elif ph < 5.5: diagnoses.append({"level": "warn", "msg": f"pH {ph} 偏酸，建议施用石灰"})
        else: diagnoses.append({"level": "ok", "msg": f"pH {ph}，注意调节"})
    if soil.get("slope") is not None:
        sl = soil["slope"]
        if sl > 15: diagnoses.append({"level": "warn", "msg": f"坡度 {sl:.1f}° 较陡，注意水土流失"})

    # ── 处方（含腐解剂推荐 + 天数） ──
    soc_val = soil.get("soc") if soil.get("soc") is not None else 20
    ph_val = soil.get("ph") if soil.get("ph") is not None else 7
    prescriptions = []

    # 从数据库加载腐解剂并按条件匹配
    from app.models.decomposer_type import DecomposerType
    from sqlalchemy import select as _select
    texture_name = soil.get("texture_name", "壤土")
    decomposer = {"name": "通用腐解剂", "dosage": 2.5, "days": 20, "features": ["通用型"]}
    try:
        _result = await db.execute(_select(DecomposerType))
        _all = list(_result.scalars().all())
        for d in _all:
            name = d.name or ""
            features = (d.features or "").split(",") if d.features else []
            if "黏" in (texture_name or "") and ("疏松" in name or "K1" in name):
                decomposer = {"name": name, "dosage": 2.2, "days": 16, "features": features}
                break
            elif "砂" in (texture_name or "") and ("保水" in name or "S1" in name):
                decomposer = {"name": name, "dosage": 3.5, "days": 22, "features": features}
                break
            elif soc_val > 25 and ("高肥" in name or "B2" in name):
                decomposer = {"name": name, "dosage": 2.5, "days": 15, "features": features}
                break
        else:
            # 没匹配到就用第一条
            if _all:
                d = _all[0]
                decomposer = {"name": d.name, "dosage": 2.8, "days": 20, "features": (d.features or "").split(",") if d.features else ["通用型"]}
    except Exception:
        pass

    # 温度修正腐解天数（从天气接口获取真实温度，3秒超时）
    temp = 20
    try:
        from app.services.weather.weather_service import WeatherService
        w = await asyncio.wait_for(
            WeatherService().get_current_weather(lat, lon),
            timeout=1.5
        )
        if w and w.get("temperature_c") is not None:
            temp = w["temperature_c"]
    except (asyncio.TimeoutError, Exception):
        pass
    if temp > 25: decomposer["days"] = max(10, decomposer["days"] - 3)
    elif temp < 10: decomposer["days"] += 5

    prescriptions.append({
        "action": f"推荐 {decomposer['name']}",
        "detail": f"用量 {decomposer['dosage']} kg/亩，预计 {decomposer['days']} 天完成腐解",
        "decomposer": decomposer
    })

    if soc_val > 25:
        prescriptions.append({"action": "维持现有策略", "detail": "有机质充足，每年秸秆还田 150kg/亩即可"})
    else:
        prescriptions.append({"action": "增施有机肥", "detail": "配合腐解剂，建议增施有机肥 200kg/亩"})
    if ph_val < 5.5:
        prescriptions.append({"action": "石灰调节", "detail": "建议施用石灰 50-80 kg/亩，分2次施入"})

    # ── 预测 ──
    base_yield = {"玉米": 650, "大豆": 220, "水稻": 550, "小麦": 400, "棉花": 300, "花生": 280}.get(crop, 500)
    soc_factor = 1 + (soc_val - 20) * 0.01
    slope_penalty = max(0, 1 - (soil.get("slope") or 5) * 0.02)
    pred_yield = round(base_yield * soc_factor * slope_penalty)
    straw_per_mu = pred_yield * 1.2  # 秸秆量 kg/亩
    carbon_per_mu = straw_per_mu * 0.44 * 0.18 * 3.67 / 1000  # tCO2e/亩
    total_carbon = round(carbon_per_mu * area_mu, 1)

    return {
        "location": {"lon": lon, "lat": lat},
        "crop": crop, "area_mu": area_mu,
        "soil_profile": soil,
        "diagnoses": diagnoses,
        "prescriptions": prescriptions,
        "predictions": {
            "yield_kg_per_mu": pred_yield,
            "carbon_tco2e_per_year": total_carbon,
            "estimated_revenue_cny": round(total_carbon * 30),
        },
        "generated_at": __import__("datetime").datetime.now().isoformat(),
    }


@router.get("/ndvi-timeline")
async def ndvi_timeline(
    lon: float = Query(...),
    lat: float = Query(...),
    years: int = Query(5, ge=1, le=10),
    current_user: dict | None = Depends(get_optional_user),
):
    """基于 DEM 推导的 NDVI 多年时间序列"""
    import math, random as _random_mod
    svc = RasterService()
    dem = await svc.read_at_point_async("dem", lon, lat) or 200
    slope = await svc.read_at_point_async("slope", lon, lat) or 5
    landuse = await svc.read_at_point_async("landuse", lon, lat) or 1

    # 基础 NDVI 由海拔和坡度决定
    base_ndvi = 0.78 - abs(dem - 200) * 0.0004 - slope * 0.008
    if landuse == 1: base_ndvi += 0.05   # 耕地
    elif landuse == 2: base_ndvi += 0.12  # 林地
    base_ndvi = max(0.2, min(0.9, base_ndvi))

    timeline = []
    _rng = _random_mod.Random(int(lon * 1000 + lat * 1000))
    for y in range(years):
        year_data = []
        for month in range(1, 13):
            seasonal = 0.12 * math.sin(2 * math.pi * (month - 3) / 12)
            ndvi = round(base_ndvi + seasonal + _rng.uniform(-0.04, 0.04), 3)
            year_data.append({"month": month, "ndvi": max(0.1, min(0.95, ndvi))})
        timeline.append({"year": 2026 - years + y + 1, "monthly": year_data,
                         "annual_mean": round(sum(d["ndvi"] for d in year_data) / 12, 3)})

    return {
        "location": {"lon": lon, "lat": lat},
        "dem": dem, "slope": slope, "landuse": int(landuse),
        "base_ndvi": round(base_ndvi, 3),
        "timeline": timeline,
    }
