"""
外部 API 数据服务 — 替代本地 GeoTIFF 文件
优先级: .tif → API → 合成数据

接入的免费 API:
- Open-Meteo Elevation: 高程 DEM
- SoilGrids (ISRIC): 土壤有机碳、pH、砂粒、粉粒、粘粒
- 坡度/坡向: 基于 DEM 本地计算

代理支持: 设置环境变量 HTTPS_PROXY 或 API_PROXY
例如: HTTPS_PROXY=http://127.0.0.1:7890
"""
import asyncio
import math
import os
import time
from datetime import datetime

import httpx

# ── 代理配置 ──
_PROXY = os.getenv("API_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")

# ── 内存缓存 ──
_cache: dict[str, tuple[float, object]] = {}
_CACHE_TTL = 86400  # 24 小时（土壤数据变化极慢）


def _cache_get(key: str):
    entry = _cache.get(key)
    if entry and time.time() - entry[0] < _CACHE_TTL:
        return entry[1]
    return None


def _cache_set(key: str, value):
    _cache[key] = (time.time(), value)


# ── HTTP 客户端 ──

def _client() -> httpx.AsyncClient:
    kwargs = {"timeout": 15}
    if _PROXY:
        kwargs["proxy"] = _PROXY
    return httpx.AsyncClient(**kwargs)


# ══════════════════════════════════════
# Open-Meteo Elevation API (免费, 无需 key)
# ══════════════════════════════════════

async def _fetch_elevation(lon: float, lat: float) -> float | None:
    """从 Open-Meteo 获取高程（米）"""
    cache_key = f"dem:{lon:.4f}:{lat:.4f}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    url = "https://api.open-meteo.com/v1/elevation"
    params = {"latitude": lat, "longitude": lon}
    try:
        async with _client() as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            elev = data.get("elevation")
            if elev is not None:
                # API 返回列表，即使单点也是 [value]
                val = float(elev[0] if isinstance(elev, list) else elev)
                val = round(val, 1)
                _cache_set(cache_key, val)
                return val
    except Exception:
        pass
    return None


async def _fetch_elevations_batch(points: list[tuple[float, float]]) -> dict[tuple[float, float], float]:
    """批量获取高程 — Open-Meteo 支持逗号分隔的多坐标"""
    result = {}
    uncached = []
    for lon, lat in points:
        cache_key = f"dem:{lon:.4f}:{lat:.4f}"
        cached = _cache_get(cache_key)
        if cached is not None:
            result[(lon, lat)] = cached
        else:
            uncached.append((lon, lat))

    if not uncached:
        return result

    lats = ",".join(str(lat) for _, lat in uncached)
    lons = ",".join(str(lon) for lon, _ in uncached)
    url = "https://api.open-meteo.com/v1/elevation"
    params = {"latitude": lats, "longitude": lons}
    try:
        async with _client() as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            elevs = data.get("elevation")
            if isinstance(elevs, (int, float)):
                elevs = [elevs]
            if elevs:
                for i, (lon, lat) in enumerate(uncached):
                    if i < len(elevs) and elevs[i] is not None:
                        val = round(float(elevs[i]), 1)
                        result[(lon, lat)] = val
                        _cache_set(f"dem:{lon:.4f}:{lat:.4f}", val)
    except Exception:
        pass

    return result


async def _compute_slope_aspect(lon: float, lat: float) -> tuple[float | None, float | None]:
    """基于 5 点高程差分计算坡度(°)和坡向(°)"""
    # 间距约 100m（经度方向随纬度变化）
    d = 0.001  # ~111m at equator, ~78m at 45°N
    cos_lat = math.cos(math.radians(lat))
    dx = d / cos_lat if cos_lat > 0.01 else d  # 经度间距修正
    dy = d

    points = [
        (lon, lat),          # 中心
        (lon - dx, lat),     # 左
        (lon + dx, lat),     # 右
        (lon, lat - dy),     # 下
        (lon, lat + dy),     # 上
    ]

    elevs = await _fetch_elevations_batch(points)
    center = elevs.get((lon, lat))
    left = elevs.get((lon - dx, lat))
    right = elevs.get((lon + dx, lat))
    down = elevs.get((lon, lat - dy))
    up = elevs.get((lon, lat + dy))

    if center is None or None in (left, right, down, up):
        return None, None

    # 有限差分
    dz_dx = (right - left) / (2 * dx * 111320 * cos_lat)  # 水平距离(m)
    dz_dy = (up - down) / (2 * dy * 110540)                # 垂直距离(m)

    slope_rad = math.atan(math.sqrt(dz_dx ** 2 + dz_dy ** 2))
    slope_deg = round(math.degrees(slope_rad), 1)

    # 坡向：0°=北, 90°=东, 180°=南, 270°=西
    aspect = math.degrees(math.atan2(-dz_dy, dz_dx))  # 注意符号
    if aspect < 0:
        aspect += 360
    aspect = round(aspect, 1)

    return slope_deg, aspect


# ══════════════════════════════════════
# SoilGrids REST API (免费, 无需 key)
# ══════════════════════════════════════

# SoilGrids 属性名映射: (API属性名, 缩放因子)
# SoilGrids 返回值单位: soc=dg/kg, phh2o=pH*10, sand/silt/clay=g/kg
_SOILGRIDS_PROPS = {
    "soc": ("soc", 0.1),       # dg/kg → g/kg
    "ph": ("phh2o", 0.1),      # pH*10 → pH
    "sand": ("sand", 0.1),     # g/kg → %
    "silt": ("silt", 0.1),     # g/kg → %
    "clay": ("clay", 0.1),     # g/kg → %
}


async def _fetch_soilgrids(lon: float, lat: float) -> dict[str, float | None]:
    """从 SoilGrids 获取土壤属性（15-30cm 深度，代表 0-30cm 层）"""
    cache_key = f"soil:{lon:.4f}:{lat:.4f}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    props = ["soc", "phh2o", "sand", "silt", "clay"]
    params = {
        "lon": lon,
        "lat": lat,
        "property": props,
        "depth": "15-30cm",
        "value": "mean",
    }

    result = {k: None for k in _SOILGRIDS_PROPS}

    try:
        async with _client() as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        layers = data.get("properties", {}).get("layers", [])
        for layer in layers:
            prop_name = layer.get("name", "")
            depths = layer.get("depths", [])
            if not depths:
                continue
            val = depths[0].get("values", {}).get("mean")
            if val is None:
                continue
            for our_name, (sg_name, scale) in _SOILGRIDS_PROPS.items():
                if prop_name == sg_name:
                    result[our_name] = round(float(val) * scale, 1)
                    break

        _cache_set(cache_key, result)
    except Exception:
        pass

    return result


# ══════════════════════════════════════
# 统一接口 — 与 synthetic_data.read_at_point 兼容
# ══════════════════════════════════════

async def api_read_at_point(name: str, lon: float, lat: float) -> float | int | None:
    """API 数据点查询 — 与 RasterService.read_at_point 接口一致"""
    if name == "dem":
        return await _fetch_elevation(lon, lat)
    elif name == "slope":
        slope, _ = await _compute_slope_aspect(lon, lat)
        return slope
    elif name == "aspect":
        _, aspect = await _compute_slope_aspect(lon, lat)
        return aspect
    elif name in ("soc", "ph", "sand", "silt", "clay"):
        soil = await _fetch_soilgrids(lon, lat)
        return soil.get(name)
    # landuse, texture — 无免费 API，返回 None 让合成数据处理
    return None


async def api_read_soil_profile(lon: float, lat: float) -> dict | None:
    """API 土壤剖面查询 — 与 RasterService.read_soil_profile 接口一致"""
    # 并行获取高程和土壤数据
    elev_task = _fetch_elevation(lon, lat)
    soil_task = _fetch_soilgrids(lon, lat)
    slope_task = _compute_slope_aspect(lon, lat)

    elev, soil, (slope, aspect) = await asyncio.gather(
        elev_task, soil_task, slope_task
    )

    # 如果核心土壤数据全部为空，返回 None（让合成数据处理）
    if all(soil.get(k) is None for k in ("soc", "ph", "sand", "silt", "clay")):
        return None

    from app.services.raster import LANDUSE_NAMES, RasterService
    from app.services import synthetic_data as _synth

    # landuse 用合成数据（无免费 API）
    lu = _synth.synthetic_landuse(lon, lat)

    profile = {
        "location": {"lon": lon, "lat": lat},
        "analyzed_at": datetime.now().isoformat(),
        "dem": elev,
        "slope": slope,
        "aspect": aspect,
        "landuse": lu,
        "landuse_name": LANDUSE_NAMES.get(lu, "未知"),
        "soc": soil.get("soc"),
        "sand": soil.get("sand"),
        "silt": soil.get("silt"),
        "clay": soil.get("clay"),
        "ph": soil.get("ph"),
    }

    tex_code, tex_name = RasterService._classify_texture(
        profile["sand"], profile["silt"], profile["clay"])
    profile["texture"] = tex_code
    profile["texture_name"] = tex_name

    soc_val = profile["soc"] if profile["soc"] is not None else 20
    profile["soil_grade"] = "优等 · 高肥力" if soc_val > 25 else \
        ("良好" if soc_val > 15 else "一般 · 需改良")

    return profile
