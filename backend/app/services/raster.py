"""
Real 30m WGS84 raster data service.
Reads GeoTIFF files directly — no database dependency.
当文件不存在时自动降级到合成数据。
"""
import math
import io
from pathlib import Path

import numpy as np

from app.core.config import get_settings

settings = get_settings()
DATA_DIR = Path(settings.RASTER_DATA_DIR)

# 惰性导入 rasterio — 降级到合成数据时不需要
try:
    import rasterio
    from rasterio.windows import Window
    _HAS_RASTERIO = True
except ImportError:
    _HAS_RASTERIO = False

# 合成数据降级
from app.services import synthetic_data as _synth
# API 数据服务
from app.services import api_data as _api

RASTER_CONFIG = {
    "dem":     {"file": "dem_30m.tif",     "desc": "东北地形高程 DEM (30m, WGS84)"},
    "slope":   {"file": "slope_30m.tif",   "desc": "坡度 (30m, WGS84)"},
    "aspect":  {"file": "aspect_30m.tif",  "desc": "坡向 (30m, WGS84)"},
    "landuse": {"file": "landuse_30m.tif", "desc": "土地利用 CLCD 30m (武汉大学)"},
    "soc":     {"file": "soc_30m.tif",     "desc": "土壤有机碳含量 0-30cm (SoilGrids, g/kg)"},
    "sand":    {"file": "sand_30m.tif",    "desc": "砂粒含量 0-30cm (SoilGrids, %)"},
    "silt":    {"file": "silt_30m.tif",    "desc": "粉粒含量 0-30cm (SoilGrids, %)"},
    "clay":    {"file": "clay_30m.tif",    "desc": "粘粒含量 0-30cm (SoilGrids, %)"},
    "ph":      {"file": "ph_30m.tif",      "desc": "土壤 pH 值"},
    "texture": {"file": "texture_30m.tif", "desc": "土壤质地分类"},
}

WGS_BOUNDS = {
    "left": 109.94912535327929, "bottom": 35.590573007334775,
    "right": 141.7516942161061, "top": 56.37077664606018,
}

LANDUSE_NAMES = {0: "冰雪/裸地", 1: "耕地", 2: "林地", 3: "草地", 4: "灌木",
                 5: "湿地", 6: "水体", 7: "苔原", 8: "建设用地", 9: "裸地"}

_raster_cache = {}


def close_all_rasters():
    """Close all cached rasterio datasets to free file handles."""
    for src in _raster_cache.values():
        try:
            src.close()
        except Exception:
            pass
    _raster_cache.clear()


class RasterService:
    """Stateless service for reading 30m WGS84 GeoTIFF raster layers."""

    _files_available: bool | None = None  # 类级别缓存：文件是否存在

    def _has_files(self) -> bool:
        if self._files_available is not None:
            return self._files_available
        if not _HAS_RASTERIO:
            self._files_available = False
            return False
        # 检查至少一个文件存在
        for cfg in RASTER_CONFIG.values():
            if (DATA_DIR / cfg["file"]).exists():
                self._files_available = True
                return True
        self._files_available = False
        return False

    def _get_src(self, name: str):
        if not _HAS_RASTERIO or not self._has_files():
            return None
        if name in _raster_cache:
            return _raster_cache[name]
        cfg = RASTER_CONFIG.get(name)
        if not cfg:
            return None
        path = DATA_DIR / cfg["file"]
        if not path.exists():
            return None
        _raster_cache[name] = rasterio.open(path)
        return _raster_cache[name]

    # ── point queries ──

    def read_at_point(self, name: str, lon: float, lat: float) -> float | None:
        src = self._get_src(name)
        if src is None:
            # 降级到合成数据
            if name in _synth._SYNTH_FUNCTIONS:
                return _synth.read_at_point(name, lon, lat)
            return None
        try:
            row, col = src.index(lon, lat)
            if 0 <= row < src.height and 0 <= col < src.width:
                val = src.read(1, window=((row, row + 1), (col, col + 1)))
                v = float(val[0, 0])
                if src.nodata is not None and v == src.nodata:
                    return None
                return v
        except Exception:
            pass
        return None

    async def read_at_point_async(self, name: str, lon: float, lat: float) -> float | None:
        """异步版本: .tif → API → 合成数据"""
        src = self._get_src(name)
        if src is not None:
            try:
                row, col = src.index(lon, lat)
                if 0 <= row < src.height and 0 <= col < src.width:
                    val = src.read(1, window=((row, row + 1), (col, col + 1)))
                    v = float(val[0, 0])
                    if src.nodata is not None and v == src.nodata:
                        return None
                    return v
            except Exception:
                pass
        # .tif 不可用，尝试 API
        try:
            val = await _api.api_read_at_point(name, lon, lat)
            if val is not None:
                return val
        except Exception:
            pass
        # API 也失败，降级到合成数据
        if name in _synth._SYNTH_FUNCTIONS:
            return _synth.read_at_point(name, lon, lat)
        return None

    # ── stats ──

    def read_stats(self, name: str) -> dict | None:
        src = self._get_src(name)
        if src is None:
            return _synth.read_stats(name)
        if src.overviews(1):
            ovr = src.overviews(1)[-1]
            data = src.read(1, out_shape=(src.height // ovr, src.width // ovr), masked=True)
        else:
            step = max(1, min(src.height, src.width) // 2000)
            data = src.read(1, masked=True, out_shape=(src.height // step, src.width // step))
        b = src.bounds
        return {
            "width": src.width, "height": src.height,
            "crs": str(src.crs),
            "bounds": [b.left, b.bottom, b.right, b.top],
            "resolution": f"{abs(src.transform[0]):.6f}° (~{abs(src.transform[0]) * 111320:.0f}m)",
            "min": float(data.min()), "max": float(data.max()),
            "mean": float(data.mean()), "std": float(data.std()),
        }

    # ── Stats cache ──
    _stats_cache: dict = {}

    def read_stats_from_db(self, name: str) -> dict | None:
        """内存缓存：首次从文件计算，后续从缓存读取"""
        return self._stats_cache.get(name)

    def save_stats_to_db(self, name: str, stats: dict) -> None:
        """缓存到内存，避免重复计算"""
        self._stats_cache[name] = {k: v for k, v in stats.items() if v is not None}

    # ── ROI ──

    def read_roi(self, name: str, lon_min: float, lat_min: float,
                 lon_max: float, lat_max: float):
        src = self._get_src(name)
        if src is None:
            # 合成数据降级：生成小网格
            rows, cols = 16, 16
            data = np.zeros((rows, cols), dtype=np.float32)
            for ri in range(rows):
                for ci in range(cols):
                    lo = lon_min + (lon_max - lon_min) * ci / cols
                    la = lat_min + (lat_max - lat_min) * ri / rows
                    v = self.read_at_point(name, lo, la) or 0
                    data[ri, ci] = v
            return data, None
        try:
            r1, c1 = src.index(lon_min, lat_max)
            r2, c2 = src.index(lon_max, lat_min)
            rm, rM = max(0, min(r1, r2)), min(src.height, max(r1, r2))
            cm, cM = max(0, min(c1, c2)), min(src.width, max(c1, c2))
            w = Window(cm, rm, max(1, cM - cm), max(1, rM - rm))
            data = src.read(1, window=w, masked=True)
            return data, w
        except Exception:
            pass
        return np.zeros((10, 10)), None

    # ── tile ──

    def generate_tile(self, name: str, z: int, x: int, y: int,
                      colormap: str = "viridis") -> bytes:
        n = 2 ** z
        lon_min = x / n * 360.0 - 180.0
        lon_max = (x + 1) / n * 360.0 - 180.0
        lat_min = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
        lat_max = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))

        data, _ = self.read_roi(name, lon_min, lat_min, lon_max, lat_max)
        data = data.filled(0) if hasattr(data, 'filled') else np.array(data)

        try:
            from PIL import Image
            img = Image.fromarray(data.astype(np.float32))
            img = img.resize((256, 256), Image.Resampling.BILINEAR)
            arr = np.array(img)
        except Exception:
            arr = data[:256, :256]

        dmin, dmax = arr.min(), arr.max()
        ndata = ((arr - dmin) / (dmax - dmin) * 255).astype(np.uint8) if dmax > dmin \
            else np.zeros_like(arr, dtype=np.uint8)

        return self._apply_colormap(ndata, colormap)

    def _apply_colormap(self, data: np.ndarray, cmap: str) -> bytes:
        from PIL import Image
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.cm as mpl_cm
        cmap_func = mpl_cm.get_cmap(cmap)
        rgba = cmap_func(data / 255.0)
        rgba_uint8 = (rgba * 255).astype(np.uint8)
        img = Image.fromarray(rgba_uint8, 'RGBA')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()

    # ── soil profile ──

    @staticmethod
    def _classify_texture(sand, silt, clay):
        if sand is None or silt is None or clay is None:
            return 2, "壤土"
        s, si, c = sand, silt, clay
        if s > 85 and si + 1.5 * c < 15: return 1, "砂土"
        if s >= 70 and (si + 2 * c <= 30): return 1, "砂壤土"
        if c >= 40 and s <= 45 and si <= 40: return 3, "黏土"
        if c >= 35 and s <= 20: return 3, "粉黏土"
        if c >= 28 and s > 20 and s <= 45: return 3, "黏壤土"
        if c >= 20 and s <= 20 and si >= 40: return 2, "粉壤土"
        if c >= 20 and s > 45 and s <= 80: return 2, "壤土"
        if c >= 12 and s <= 20 and si >= 50: return 2, "粉壤土"
        if c >= 12 and s > 52: return 1, "砂壤土"
        if c >= 7 and s <= 50 and si >= 50: return 2, "粉壤土"
        if c >= 7 and s > 50: return 1, "砂壤土"
        if c < 7 and s > 50: return 1, "砂土"
        if c < 7 and si >= 80: return 2, "粉土"
        return 2, "壤土"

    def read_soil_profile(self, lon: float, lat: float) -> dict:
        from datetime import datetime
        profile = {
            "location": {"lon": lon, "lat": lat},
            "analyzed_at": datetime.now().isoformat(),
        }
        profile["dem"] = self.read_at_point("dem", lon, lat)
        profile["slope"] = self.read_at_point("slope", lon, lat)
        profile["aspect"] = self.read_at_point("aspect", lon, lat)
        lu = self.read_at_point("landuse", lon, lat)
        profile["landuse"] = int(lu) if lu is not None else None
        profile["soc"] = self.read_at_point("soc", lon, lat)
        profile["sand"] = self.read_at_point("sand", lon, lat)
        profile["silt"] = self.read_at_point("silt", lon, lat)
        profile["clay"] = self.read_at_point("clay", lon, lat)
        profile["ph"] = self.read_at_point("ph", lon, lat)

        tex_code, tex_name = self._classify_texture(
            profile["sand"], profile["silt"], profile["clay"])
        profile["texture"] = tex_code
        profile["texture_name"] = tex_name
        profile["landuse_name"] = LANDUSE_NAMES.get(profile["landuse"], "未知") \
            if profile["landuse"] is not None else "未知"

        soc_val = profile["soc"] if profile["soc"] is not None else 20
        profile["soil_grade"] = "优等 · 高肥力" if soc_val > 25 else \
            ("良好" if soc_val > 15 else "一般 · 需改良")

        return profile

    async def read_soil_profile_async(self, lon: float, lat: float) -> dict:
        """异步版本: .tif → API → 合成数据"""
        # 如果有 .tif 文件，用同步版本（最快）
        if self._has_files():
            return self.read_soil_profile(lon, lat)

        # 尝试 API 获取完整土壤剖面
        try:
            profile = await _api.api_read_soil_profile(lon, lat)
            if profile is not None:
                return profile
        except Exception:
            pass

        # API 失败，用合成数据（逐层查询，每层都会走合成降级）
        return self.read_soil_profile(lon, lat)
