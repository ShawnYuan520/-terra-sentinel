"""天气服务 — OpenWeather API + 模拟降级（含地理相关性）"""
import hashlib
import random
import time
import httpx
from datetime import datetime, timezone, timedelta
from app.core.config import get_settings

# ── 服务层缓存（所有调用方共享）──
_weather_cache: dict[str, tuple[float, object]] = {}
_CACHE_TTL_CURRENT = 600    # 当前天气 10 分钟
_CACHE_TTL_FORECAST = 1800  # 预报 30 分钟
_CACHE_TTL_AGRI = 1800      # 农业气象 30 分钟


def _cache_get(key: str):
    entry = _weather_cache.get(key)
    if entry and time.time() < entry[0]:
        return entry[1]
    return None


def _cache_set(key: str, value, ttl: float):
    _weather_cache[key] = (time.time() + ttl, value)


def _lat_seeded(lat: float, lon: float, offset: str = "") -> random.Random:
    """创建与经纬度绑定的确定性随机数生成器"""
    seed_str = f"{lat:.3f}:{lon:.3f}:{offset}"
    seed_val = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    return random.Random(seed_val)


# ── 地理相关的温度估算 ──
def _est_temperature(lat: float, lon: float, month: int) -> float:
    """根据纬度+月份估算日均温（中国东北地区参考）"""
    # 年温范围: 哈尔滨(45.8°N) ~ -18~23°C, 北京(39.9°N) ~ -4~26°C
    annual_range = 32 - (lat - 20) * 0.3  # 低纬度年较差小
    summer_peak = 28 - (lat - 20) * 0.6  # 夏季最高温
    # 正弦年周期: 峰值在7月(month=7)
    seasonal = summer_peak - annual_range / 2 + annual_range / 2 * __import__("math").sin(
        (month - 4) * __import__("math").pi / 6
    )
    return round(seasonal, 1)


class WeatherService:
    """聚合天气数据。有 API Key 用 OpenWeather，无 Key 降级为模拟数据。"""

    def __init__(self):
        self.key = get_settings().OPENWEATHER_API_KEY
        self.base = "https://api.openweathermap.org/data/2.5"
        self._real = bool(self.key)

    async def _ow_get(self, endpoint: str, params: dict) -> dict | None:
        """调用 OpenWeather API"""
        if not self._real:
            return None
        params["appid"] = self.key
        params["units"] = "metric"
        params["lang"] = "zh_cn"
        try:
            async with httpx.AsyncClient(timeout=3) as c:
                r = await c.get(f"{self.base}/{endpoint}", params=params)
                if r.status_code == 200:
                    return r.json()
        except Exception:
            pass
        return None

    async def get_current_weather(self, lat: float, lon: float) -> dict:
        """当前天气"""
        cache_key = f"current:{lat:.2f}:{lon:.2f}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        data = await self._ow_get("weather", {"lat": lat, "lon": lon})
        if data:
            result = {
                "location": {"lat": lat, "lon": lon},
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "temperature_c": data["main"]["temp"],
                "humidity_pct": data["main"]["humidity"],
                "pressure_hpa": data["main"]["pressure"],
                "precipitation_mm": data.get("rain", {}).get("1h", 0),
                "wind_speed_ms": data["wind"]["speed"],
                "wind_direction_deg": data["wind"].get("deg", 0),
                "description": data["weather"][0]["description"],
                "icon": data["weather"][0]["icon"],
                "clouds_pct": data["clouds"]["all"],
                "visibility_m": data.get("visibility", 10000),
                "source": "OpenWeather"
            }
        else:
            # 模拟降级 — 含地理季节性相关性
            rng = _lat_seeded(lat, lon, "current")
            month = datetime.now(timezone.utc).month
            temp = _est_temperature(lat, lon, month) + rng.uniform(-3, 3)
            humidity = int(50 + (45 - lat) * 2 + rng.randint(-10, 10))
            humidity = max(30, min(95, humidity))

            # 夏季多雨，冬季少雨
            if 6 <= month <= 9:
                precip = rng.uniform(0, 12)
            elif month in (4, 5, 10):
                precip = rng.uniform(0, 6)
            else:
                precip = rng.uniform(0, 3)

            desc = "晴"
            if precip > 5:
                desc = "中雨" if precip > 8 else "小雨"
            elif humidity > 80:
                desc = "多云" if rng.random() > 0.5 else "阴"

            result = {
                "location": {"lat": lat, "lon": lon},
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "temperature_c": round(temp, 1),
                "humidity_pct": humidity,
                "pressure_hpa": rng.randint(1005, 1028),
                "precipitation_mm": round(precip, 1),
                "wind_speed_ms": round(rng.uniform(0.5, 7), 1),
                "wind_direction_deg": rng.randint(0, 360),
                "description": desc,
                "icon": "01d",
                "clouds_pct": min(100, int(humidity * 1.2)),
                "visibility_m": rng.randint(6000, 10000),
                "source": "simulated"
            }

        _cache_set(cache_key, result, _CACHE_TTL_CURRENT)
        return result

    async def get_forecast(self, lat: float, lon: float, days: int = 5) -> list[dict]:
        """5 天预报（每 3 小时一个点，聚合为每日数据）"""
        cache_key = f"forecast:{lat:.2f}:{lon:.2f}:{days}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        data = await self._ow_get("forecast", {"lat": lat, "lon": lon, "cnt": min(days * 8, 40)})
        if data:
            days_data: dict[str, dict] = {}
            for item in data["list"]:
                date_str = item["dt_txt"][:10]
                if date_str not in days_data:
                    days_data[date_str] = {"temps": [], "humidity": [], "precip": [], "wind": [], "desc": []}
                d = days_data[date_str]
                d["temps"].append(item["main"]["temp"])
                d["humidity"].append(item["main"]["humidity"])
                d["precip"].append(item.get("rain", {}).get("3h", 0))
                d["wind"].append(item["wind"]["speed"])
                d["desc"].append(item["weather"][0]["description"])

            forecast = []
            for date_str, d in sorted(days_data.items())[:days]:
                forecast.append({
                    "date": date_str,
                    "temp_max": round(max(d["temps"]), 1),
                    "temp_min": round(min(d["temps"]), 1),
                    "precipitation_mm": round(sum(d["precip"]), 1),
                    "humidity_pct": int(sum(d["humidity"]) / len(d["humidity"])),
                    "wind_speed_ms": round(sum(d["wind"]) / len(d["wind"]), 1),
                    "description": max(set(d["desc"]), key=d["desc"].count),
                })
        else:
            # 模拟降级 — 含地理相关性
            rng = _lat_seeded(lat, lon, "forecast")
            now = datetime.now(timezone.utc)
            forecast = []
            for day_idx in range(1, days + 1):
                date = now + timedelta(days=day_idx)
                month = date.month
                temp = _est_temperature(lat, lon, month) + rng.uniform(-4, 4)
                forecast.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "temp_max": round(temp + rng.uniform(2, 5), 1),
                    "temp_min": round(temp - rng.uniform(3, 7), 1),
                    "precipitation_mm": round(rng.uniform(0, 8) if 5 <= month <= 9 else rng.uniform(0, 3), 1),
                    "humidity_pct": int(min(95, max(30, 55 + (45 - lat) * 2 + rng.randint(-15, 15)))),
                    "wind_speed_ms": round(rng.uniform(0.5, 7), 1),
                    "description": rng.choice(["晴", "多云", "小雨", "阴", "晴"]),
                })

        _cache_set(cache_key, forecast, _CACHE_TTL_FORECAST)
        return forecast

    async def get_agricultural_weather(self, lat: float, lon: float) -> dict:
        """农业气象指标 — 从天气数据推算"""
        cache_key = f"agri:{lat:.2f}:{lon:.2f}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        current = await self.get_current_weather(lat, lon)
        temp_c = current["temperature_c"]

        from datetime import datetime as dt
        month = dt.now().month
        days_in_season = (month - 3) * 30 if month > 3 else 0
        gdd = max(0, (temp_c - 10) * days_in_season) if days_in_season > 0 else 0

        humidity = current["humidity_pct"]
        precip = current["precipitation_mm"]
        if humidity < 30 and precip < 1:
            drought_risk = "high"
        elif humidity < 50 and precip < 3:
            drought_risk = "moderate"
        else:
            drought_risk = "low"

        frost_risk = "none"
        if temp_c < 5:
            frost_risk = "high"
        elif temp_c < 10:
            frost_risk = "low"

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "growing_degree_days": round(gdd, 1),
            "soil_moisture_percentile": current["humidity_pct"],
            "drought_risk": drought_risk,
            "frost_risk": frost_risk,
        }
        _cache_set(cache_key, result, _CACHE_TTL_AGRI)
        return result
