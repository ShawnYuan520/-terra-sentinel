"""空间数据 API"""
import json
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_optional_user
from app.core.cache import raster_cache
from app.services.geo.postgis import PostGISSpatialService
from app.services.gee.gee_service import GEEService

router = APIRouter(prefix="/geo", tags=["空间服务"])


def _field_centroid(geom_text: str):
    """从 GeoJSON 文本提取中心点"""
    try:
        g = json.loads(geom_text)
        if g["type"] == "Polygon":
            coords = g["coordinates"][0]
            cx = sum(c[0] for c in coords) / len(coords)
            cy = sum(c[1] for c in coords) / len(coords)
            return cx, cy
    except Exception:
        pass
    return None, None


@router.get("/fields/{field_id}")
async def get_field_info(
    field_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user),
):
    svc = PostGISSpatialService(db)
    info = await svc.get_field_geom(field_id)
    if not info:
        raise HTTPException(404, "田块不存在")
    return info


@router.get("/viewport")
async def get_fields_in_viewport(
    xmin: float = Query(...), ymin: float = Query(...),
    xmax: float = Query(...), ymax: float = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user),
):
    svc = PostGISSpatialService(db)
    user_id = current_user["sub"] if current_user else None
    return await svc.get_fields_in_viewport(xmin, ymin, xmax, ymax, user_id)


@router.get("/ndvi/{field_id}")
async def get_ndvi_timeseries(
    field_id: str,
    days: int = Query(90, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user),
):
    # 缓存 NDVI 时序（Sentinel-2 数据更新频率低）
    cache_key = f"ndvi:{field_id}:{days}"
    cached = await raster_cache.get(cache_key)
    if cached is not None:
        return cached

    svc = PostGISSpatialService(db)
    info = await svc.get_field_geom(field_id)
    if not info:
        raise HTTPException(404, "田块不存在")
    lon, lat = _field_centroid(info.get("geom", ""))
    if lon is None or lat is None:
        raise HTTPException(400, "无法解析田块中心坐标")
    gee = GEEService()
    result = await gee.get_ndvi_timeseries(field_id, lon, lat, days)
    if result:
        await raster_cache.set(cache_key, result, ttl=3600)  # 1小时缓存
    return result


@router.get("/landcover/{field_id}")
async def get_land_cover(
    field_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user),
):
    cache_key = f"lc:{field_id}"
    cached = await raster_cache.get(cache_key)
    if cached is not None:
        return cached

    svc = PostGISSpatialService(db)
    info = await svc.get_field_geom(field_id)
    if not info:
        raise HTTPException(404, "田块不存在")
    lon, lat = _field_centroid(info.get("geom", ""))
    if lon is None or lat is None:
        raise HTTPException(400, "无法解析田块中心坐标")
    gee = GEEService()
    result = await gee.get_land_cover(field_id, lon, lat)
    if result:
        await raster_cache.set(cache_key, result, ttl=86400)  # 土地覆盖很稳定，24h缓存
    return result
