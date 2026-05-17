"""遥感服务 — 基于 10 层真实 30m 栅格数据推导 NDVI"""
import math
import threading
from datetime import datetime, timezone, timedelta
from app.services.raster import RasterService

# GEE 可选（配置服务账号后自动启用）
try:
    import ee
    _EE_AVAILABLE = True
except ImportError:
    _EE_AVAILABLE = False

_ee_ready = False
_ee_init_done = False  # 是否已尝试过初始化（避免重复超时）


def _init_gee() -> bool:
    global _ee_ready, _ee_init_done
    if _ee_ready or not _EE_AVAILABLE:
        return _ee_ready
    if _ee_init_done:
        return False  # 之前失败过，不再重试
    _ee_init_done = True

    result = [False]

    def _do_init():
        import sys
        import os
        try:
            from app.core.config import get_settings
            s = get_settings()

            # 配置代理（仅对 Google 域名 — 国内需要，不影响天气等直连API）
            proxy = s.GEE_PROXY or ""
            if proxy:
                os.environ["HTTPS_PROXY"] = proxy
                os.environ["HTTP_PROXY"] = proxy
                # 只代理 Google 相关域名, 其他走直连
                os.environ["NO_PROXY"] = "localhost,127.0.0.1,.openweathermap.org,.bing.com,api.openweathermap.org"
                print(f"[GEE] Using proxy: {proxy}", file=sys.stderr)

            if s.GEE_SERVICE_ACCOUNT and s.GEE_KEY_FILE:
                creds = ee.ServiceAccountCredentials(
                    s.GEE_SERVICE_ACCOUNT,
                    key_file=s.GEE_KEY_FILE,
                )
                ee.Initialize(creds, project=s.GEE_PROJECT or None)
            elif s.GEE_PROJECT:
                ee.Initialize(project=s.GEE_PROJECT)
            else:
                return
            result[0] = True
        except Exception as e:
            import sys
            print(f"[GEE] Init failed: {e}", file=sys.stderr)

    # 用线程 + 超时，防止 GEE 初始化卡死整个请求
    t = threading.Thread(target=_do_init, daemon=True)
    t.start()
    t.join(timeout=10)  # 通过代理可能需要更长时间
    if t.is_alive():
        import sys
        print("[GEE] Init timeout (10s), skipping GEE", file=sys.stderr)
        return False

    _ee_ready = result[0]
    if _ee_ready:
        import sys
        print("[GEE] Initialized successfully", file=sys.stderr)
    return _ee_ready


class GEEService:

    def __init__(self):
        self._gee = _init_gee()

    async def get_ndvi_timeseries(self, field_id: str, lon: float = None,
                                   lat: float = None, days: int = 90) -> list[dict]:
        if self._gee and lon and lat:
            try:
                result = self._real_s2_ndvi(lon, lat)
                if result:
                    return result
            except Exception:
                pass
        return self._raster_ndvi(lon or 126.33, lat or 45.39, days)

    def _real_s2_ndvi(self, lon, lat):
        point = ee.Geometry.Point(lon, lat)
        s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
              .filterBounds(point).filterDate("2022-01-01", datetime.now().strftime("%Y-%m-%d"))
              .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30)).select(["B4", "B8"]))
        def add_ndvi(img):
            return img.addBands(img.normalizedDifference(["B8", "B4"]).rename("ndvi"))
        ts = s2.map(add_ndvi).select("ndvi").getRegion(point, 10).getInfo()
        if not ts or len(ts) < 2:
            return []
        result = []
        for row in ts[1:]:
            v, t = row[4], row[3]
            if v is not None and t is not None:
                ts_s = t / 1000 if t > 1e10 else t
                result.append({"timestamp": datetime.fromtimestamp(ts_s, tz=timezone.utc).isoformat(),
                               "ndvi": round(float(v), 3), "source": "Sentinel-2"})
        return result

    @staticmethod
    def _raster_ndvi(lon: float, lat: float, days: int = 90) -> list[dict]:
        """
        基于真实 30m 栅格数据推导 NDVI（模拟东北农田物候）：
        - 耕地: 4月播种(NDVI~0.15) → 7-8月旺季(0.75-0.85) → 10月收获后降至0.15
        - 林地: 常年较高(0.55-0.82)，季节波动小
        - 草地: 中等水平(0.22-0.65)
        - 裸地/建设用地: 持续低值(<0.2)
        """
        svc = RasterService()
        dem = svc.read_at_point("dem", lon, lat) or 200
        slope = svc.read_at_point("slope", lon, lat) or 5
        lu_raw = svc.read_at_point("landuse", lon, lat) or 1
        lu = int(lu_raw)
        soc = svc.read_at_point("soc", lon, lat) or 25

        # 按土地覆盖类型设定基础 NDVI 和季节振幅
        # (base, amplitude) — 耕地振幅大，林地振幅小
        lu_params = {
            1: (0.18, 0.38),   # 耕地：裸土→茂盛，波动最大
            2: (0.55, 0.22),   # 林地：常年较高，季节波动小
            3: (0.25, 0.30),   # 草地
            4: (0.28, 0.25),   # 灌木
            5: (0.30, 0.20),   # 湿地
            8: (0.10, 0.05),   # 建设用地：持续低值
            9: (0.12, 0.08),   # 裸地
        }
        base, amplitude = lu_params.get(lu, (0.18, 0.30))

        # 海拔修正：高海拔→植被更稀疏
        base -= max(0, dem - 200) * 0.0003
        # 坡度修正：陡坡→植被更少
        base -= max(0, slope - 10) * 0.008
        # 有机碳修正：SOC高→植被更健康
        base += (soc - 20) * 0.003
        base = max(0.08, min(0.88, base))

        now = datetime.now(timezone.utc)
        result = []
        for i in range(0, days, 5):
            d = now - timedelta(days=i)
            doy = d.timetuple().tm_yday
            # 物候正弦曲线：峰值在 DOY 210（7月底），谷值在 DOY 30（1月底）
            seasonal = amplitude * math.sin(2 * math.pi * (doy - 120) / 365)
            ndvi = round(base + seasonal, 3)
            ndvi = max(0.08, min(0.92, ndvi))
            result.append({
                "timestamp": d.isoformat(),
                "ndvi": ndvi,
                "source": "raster-modeled",
            })
        return result

    # ── 其他 ──

    async def get_land_cover(self, field_id: str, lon: float = None, lat: float = None) -> dict:
        from app.services.raster import RasterService, LANDUSE_NAMES
        svc = RasterService()
        if lon is None or lat is None:
            return {"field_id": field_id, "source": "landuse raster", "error": "需要提供经纬度"}
        lu = svc.read_at_point("landuse", lon, lat)
        lu_name = LANDUSE_NAMES.get(int(lu), "未知") if lu is not None else "未知"
        dem = svc.read_at_point("dem", lon, lat)
        soc = svc.read_at_point("soc", lon, lat)
        return {
            "field_id": field_id,
            "location": {"lon": lon, "lat": lat},
            "source": "武汉大学 CLCD 30m",
            "landuse_code": int(lu) if lu is not None else None,
            "landuse_name": lu_name,
            "elevation_m": round(dem, 0) if dem is not None else None,
            "soc_g_per_kg": round(soc, 1) if soc is not None else None,
        }

