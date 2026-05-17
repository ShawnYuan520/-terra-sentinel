"""
合成地理空间数据生成器
当真实 GeoTIFF 文件不存在时，基于经纬度生成确定性、空间自相关的模拟数据。
覆盖东北黑土区（双城地区 ~126.33°E, 45.39°N）的合理数值范围。
"""
import hashlib
import math
from datetime import datetime


def _hash(lon: float, lat: float, seed: str = "") -> float:
    """确定性哈希 [0, 1) — 同一坐标+种子始终返回相同值"""
    key = f"{lon:.5f}:{lat:.5f}:{seed}"
    h = hashlib.md5(key.encode()).hexdigest()
    return int(h[:12], 16) / 0xFFF_FFF_FFF_FFF


def _noise(lon: float, lat: float, scale: float = 0.05) -> float:
    """简单空间噪声 — 相邻坐标值相近"""
    gx = math.floor(lon / scale)
    gy = math.floor(lat / scale)
    # 四个角点哈希 + 双线性插值
    fx = (lon - gx * scale) / scale
    fy = (lat - gy * scale) / scale
    v00 = _hash(gx * scale, gy * scale, "noise")
    v10 = _hash((gx + 1) * scale, gy * scale, "noise")
    v01 = _hash(gx * scale, (gy + 1) * scale, "noise")
    v11 = _hash((gx + 1) * scale, (gy + 1) * scale, "noise")
    # 平滑插值
    fx = fx * fx * (3 - 2 * fx)  # smoothstep
    fy = fy * fy * (3 - 2 * fy)
    a = v00 * (1 - fx) + v10 * fx
    b = v01 * (1 - fx) + v11 * fx
    return a * (1 - fy) + b * fy


# ── 东北地区宏观空间趋势 ──

def _trend_dem(lon: float, lat: float) -> float:
    """宏观地形趋势：松嫩平原 120-250m，东部山区渐高"""
    base = 160.0
    # 纬度趋势：越北越高（小兴安岭方向）
    base += (lat - 44.0) * 25.0
    # 经度趋势：越东越高（张广才岭方向）
    base += max(0, lon - 128.0) * 15.0
    # 哈尔滨附近微地形
    base -= max(0, 4.0 - abs(lon - 126.6) * 5 - abs(lat - 45.8) * 5) * 40.0  # 松花江河谷
    return max(80, min(600, base))


def _trend_soc(lon: float, lat: float) -> float:
    """SOC空间趋势：双城-哈尔滨黑土核心区高值，向外递减"""
    # 黑土核心区 (125.5-127.5°E, 44.5-46.5°N)
    dist_to_core = math.sqrt(
        ((lon - 126.5) / 1.5) ** 2 + ((lat - 45.5) / 1.5) ** 2
    )
    core_value = 32.0 - dist_to_core * 10.0
    return max(12, min(40, core_value))


def _trend_ph(lon: float, lat: float) -> float:
    """pH空间趋势：东北偏微酸性-中性"""
    base = 6.5 + _noise(lon, lat, 0.15) * 0.6
    return round(max(5.2, min(8.2, base)), 1)


# ── 单点合成 ──

def synthetic_dem(lon: float, lat: float) -> float:
    trend = _trend_dem(lon, lat)
    micro = _noise(lon, lat, 0.02) * 40 - 20
    return round(max(60, min(800, trend + micro)), 1)


def synthetic_slope(lon: float, lat: float) -> float:
    """合成坡度 0-30°，平原为主，偶有起伏"""
    base = 2.0
    micro = _noise(lon, lat, 0.01) * 20.0
    return round(max(0.1, min(30, base + micro)), 1)


def synthetic_aspect(lon: float, lat: float) -> float:
    """合成坡向 0-360°"""
    return round(_noise(lon, lat, 0.03) * 360, 1)


def synthetic_landuse(lon: float, lat: float) -> int:
    """合成土地利用：东北以耕地(1)为主，部分林地(2)、草地(3)"""
    v = _noise(lon, lat, 0.08)
    if v > 0.88:
        return 2  # 林地
    elif v > 0.80:
        return 3  # 草地
    elif v > 0.75:
        return 8  # 建设用地
    elif v > 0.72:
        return 5  # 湿地
    else:
        return 1  # 耕地


def synthetic_soc(lon: float, lat: float) -> float:
    soc = _trend_soc(lon, lat)
    micro = _noise(lon, lat, 0.03) * 8 - 4
    return round(max(8, min(45, soc + micro)), 1)


def synthetic_sand(lon: float, lat: float) -> float:
    """合成砂粒含量 10-60%"""
    v = 28 + _noise(lon, lat, 0.04) * 30 - 10
    return round(max(5, min(70, v)), 1)


def synthetic_silt(lon: float, lat: float) -> float:
    """合成粉粒含量 20-65%"""
    v = 42 + _noise(lon, lat, 0.05) * 25 - 8
    return round(max(15, min(70, v)), 1)


def synthetic_clay(lon: float, lat: float) -> float:
    """合成粘粒含量 15-45%"""
    v = 28 + _noise(lon, lat, 0.04) * 20 - 6
    return round(max(8, min(50, v)), 1)


def synthetic_ph(lon: float, lat: float) -> float:
    return _trend_ph(lon, lat)


def synthetic_texture_code(lon: float, lat: float) -> int:
    """合成质地分类：1=砂土 2=壤土 3=黏土 — 东北以壤土(2)为主"""
    v = _noise(lon, lat, 0.06)
    if v > 0.85:
        return 1
    elif v > 0.7:
        return 3
    return 2


# ── 统计信息（用于 /raster/list） ──

SYNTHETIC_STATS = {
    "dem":     {"min": 85.0, "max": 598.0, "mean": 178.3, "std": 62.5, "width": 3600, "height": 2400, "crs": "EPSG:4326", "resolution": "0.008333° (~927m)", "bounds": [109.95, 35.59, 141.75, 56.37]},
    "slope":   {"min": 0.1,  "max": 28.5,  "mean": 3.2,   "std": 4.1,  "width": 3600, "height": 2400, "crs": "EPSG:4326", "resolution": "0.008333° (~927m)", "bounds": [109.95, 35.59, 141.75, 56.37]},
    "aspect":  {"min": 0.0,  "max": 359.8, "mean": 178.5, "std": 104.2, "width": 3600, "height": 2400, "crs": "EPSG:4326", "resolution": "0.008333° (~927m)", "bounds": [109.95, 35.59, 141.75, 56.37]},
    "landuse": {"min": 0.0,  "max": 9.0,   "mean": 1.8,   "std": 1.5,  "width": 3600, "height": 2400, "crs": "EPSG:4326", "resolution": "0.008333° (~927m)", "bounds": [109.95, 35.59, 141.75, 56.37]},
    "soc":     {"min": 10.2, "max": 38.5,  "mean": 24.6,  "std": 5.2,  "width": 3600, "height": 2400, "crs": "EPSG:4326", "resolution": "0.008333° (~927m)", "bounds": [109.95, 35.59, 141.75, 56.37]},
    "sand":    {"min": 8.0,  "max": 62.0,  "mean": 28.5,  "std": 9.8,  "width": 3600, "height": 2400, "crs": "EPSG:4326", "resolution": "0.008333° (~927m)", "bounds": [109.95, 35.59, 141.75, 56.37]},
    "silt":    {"min": 18.0, "max": 65.0,  "mean": 41.2,  "std": 8.5,  "width": 3600, "height": 2400, "crs": "EPSG:4326", "resolution": "0.008333° (~927m)", "bounds": [109.95, 35.59, 141.75, 56.37]},
    "clay":    {"min": 10.0, "max": 45.0,  "mean": 27.8,  "std": 6.2,  "width": 3600, "height": 2400, "crs": "EPSG:4326", "resolution": "0.008333° (~927m)", "bounds": [109.95, 35.59, 141.75, 56.37]},
    "ph":      {"min": 5.2,  "max": 8.0,   "mean": 6.6,   "std": 0.5,  "width": 3600, "height": 2400, "crs": "EPSG:4326", "resolution": "0.008333° (~927m)", "bounds": [109.95, 35.59, 141.75, 56.37]},
    "texture": {"min": 1.0,  "max": 3.0,   "mean": 1.8,   "std": 0.4,  "width": 3600, "height": 2400, "crs": "EPSG:4326", "resolution": "0.008333° (~927m)", "bounds": [109.95, 35.59, 141.75, 56.37]},
}

# ── 点查询分发 ──

_SYNTH_FUNCTIONS = {
    "dem":     synthetic_dem,
    "slope":   synthetic_slope,
    "aspect":  synthetic_aspect,
    "landuse": synthetic_landuse,
    "soc":     synthetic_soc,
    "sand":    synthetic_sand,
    "silt":    synthetic_silt,
    "clay":    synthetic_clay,
    "ph":      synthetic_ph,
    "texture": synthetic_texture_code,
}


def read_at_point(name: str, lon: float, lat: float) -> float | int | None:
    """合成数据点查询 — 与 RasterService.read_at_point 接口一致"""
    fn = _SYNTH_FUNCTIONS.get(name)
    if fn is None:
        return None
    return fn(lon, lat)


def read_stats(name: str) -> dict | None:
    """合成数据统计 — 与 RasterService.read_stats 接口一致"""
    return SYNTHETIC_STATS.get(name)


LANDUSE_NAMES = {0: "冰雪/裸地", 1: "耕地", 2: "林地", 3: "草地", 4: "灌木",
                 5: "湿地", 6: "水体", 7: "苔原", 8: "建设用地", 9: "裸地"}


def read_soil_profile(lon: float, lat: float) -> dict:
    """合成土壤剖面 — 与 RasterService.read_soil_profile 接口一致"""
    sand = synthetic_sand(lon, lat)
    silt = synthetic_silt(lon, lat)
    clay = synthetic_clay(lon, lat)
    tex_code = synthetic_texture_code(lon, lat)
    # USADA 质地三角简化判断
    if sand > 50 and clay < 20:
        tex_code, tex_name = 1, "砂壤土"
    elif clay > 35:
        tex_code, tex_name = 3, "黏壤土"
    else:
        tex_code, tex_name = 2, "壤土"

    lu = synthetic_landuse(lon, lat)
    soc = synthetic_soc(lon, lat)

    # 土壤等级
    if soc > 25:
        grade = "优等 · 高肥力"
    elif soc > 15:
        grade = "良好"
    else:
        grade = "一般 · 需改良"

    return {
        "location": {"lon": lon, "lat": lat},
        "analyzed_at": datetime.now().isoformat(),
        "dem": synthetic_dem(lon, lat),
        "slope": synthetic_slope(lon, lat),
        "aspect": synthetic_aspect(lon, lat),
        "landuse": lu,
        "landuse_name": LANDUSE_NAMES.get(lu, "未知"),
        "soc": soc,
        "sand": sand,
        "silt": silt,
        "clay": clay,
        "ph": synthetic_ph(lon, lat),
        "texture": tex_code,
        "texture_name": tex_name,
        "soil_grade": grade,
    }
