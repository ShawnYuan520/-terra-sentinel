"""
CUSUM (Cumulative Sum) 物候期检测算法
参考: 冯子恒(2024). 基于无人机和卫星遥感的小麦玉米物候期监测方法研究.
- VI-RGS 模型: 玉米 R²=0.97, RMSE=5.33天
- CNN-GRU BBCH估算: R²=0.98, RMSE=3.61天
- 多源物候起始日期: 玉米 R²=0.97, RMSE=5.89天
"""
import math
from datetime import datetime


def detect_phenology(ndvi_series: list[dict]) -> dict:
    """
    输入: NDVI 时序 [{timestamp, ndvi}, ...]
    输出: {stage_name: {date, ndvi, doy}}

    检测的物候期:
    - 返青期 (green-up): NDVI 开始持续上升
    - 拔节期 (jointing): NDVI 快速上升阶段
    - 抽穗期 (heading): NDVI 接近峰值
    - 成熟期 (maturity): NDVI 峰值后下降
    - 收获期 (harvest): NDVI 快速下降
    """
    if not ndvi_series or len(ndvi_series) < 10:
        return {"error": "NDVI数据不足，需要至少10个观测点"}

    # 按时间排序，提取 NDVI 数组
    sorted_data = sorted(ndvi_series, key=lambda x: x.get("timestamp", ""))
    values = [d.get("ndvi", 0) for d in sorted_data if d.get("ndvi") is not None]
    n = len(values)

    if n < 10:
        return {"error": "有效NDVI数据不足"}

    # --- 1. 计算 CUSUM ---
    mean_ndvi = sum(values) / n
    cusum = [0.0]
    for v in values:
        cusum.append(cusum[-1] + (v - mean_ndvi))

    # --- 2. 检测变点 ---
    # 2a. 返青期: CUSUM 从持续下降转为上升的拐点
    greenup_idx = _find_greenup(cusum, values, mean_ndvi)
    # 2b. 成熟期: NDVI 峰值点
    peak_idx = values.index(max(values)) if max(values) > 0 else n - 1
    # 2c. 收获期: 峰值后 NDVI 持续下降的加速点
    harvest_idx = _find_harvest(values, cusum, peak_idx)
    # 2d. 拔节期: 返青到峰值之间，NDVI上升最快的点
    jointing_idx = _find_max_growth(values, greenup_idx, peak_idx)
    # 2e. 抽穗期: 拔节到峰值之间，NDVI增速明显减缓的点
    heading_idx = _find_heading(values, jointing_idx, peak_idx)

    result = {}
    stages = [
        ("返青期", greenup_idx, "🌱"),
        ("拔节期", jointing_idx, "📈"),
        ("抽穗期", heading_idx, "🌾"),
        ("成熟期", peak_idx, "🌽"),
        ("收获期", harvest_idx, "🚜"),
    ]

    for name, idx, emoji in stages:
        if 0 <= idx < n:
            entry = sorted_data[idx]
            ts = entry.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                doy = dt.timetuple().tm_yday
            except Exception:
                doy = -1
            result[name] = {
                "date": ts[:10] if ts else "",
                "ndvi": round(values[idx], 3),
                "doy": doy,
                "emoji": emoji,
            }

    result["_meta"] = {
        "algorithm": "CUSUM变点检测",
        "mean_ndvi": round(mean_ndvi, 3),
        "data_points": n,
    }
    return result


def _find_greenup(cusum, values, mean):
    """找返青期: CUSUM从下降到上升的转折点"""
    n = len(values)
    # 取前60%的数据找最低CUSUM点
    window = int(n * 0.6)
    if window < 5:
        return 0
    min_idx = 0
    min_val = float("inf")
    for i in range(window):
        if cusum[i] < min_val:
            min_val = cusum[i]
            min_idx = i
    # 从最低点往后找第一个 NDVI 连续上升的位置
    for i in range(min_idx, min(min_idx + 10, n - 2)):
        if values[i + 1] > values[i] and values[i] > mean * 0.6:
            return i
    return max(0, min_idx)


def _find_max_growth(values, start, end):
    """找拔节期: NDVI增速最大的点"""
    if start >= end or end - start < 2:
        return start
    max_growth = 0
    max_idx = start
    window = 5  # 5点滑动窗口
    for i in range(start, end - window):
        growth = values[i + window] - values[i]
        if growth > max_growth:
            max_growth = growth
            max_idx = i + window // 2
    return max_idx


def _find_heading(values, jointing_idx, peak_idx):
    """找抽穗期: 拔节到峰值之间, 增速减缓到原来的1/3处"""
    if jointing_idx >= peak_idx or peak_idx - jointing_idx < 2:
        return max(0, peak_idx - 2)
    # 计算拔节期增速
    early_growth = values[jointing_idx] - values[max(0, jointing_idx - 3)]
    # 找增速降到早期增速1/3的位置
    for i in range(jointing_idx, peak_idx - 1):
        current_growth = values[i + 1] - values[i]
        if current_growth < early_growth * 0.33 and values[i] > values[0] * 1.3:
            return i
    return jointing_idx + (peak_idx - jointing_idx) // 2


def _find_harvest(values, cusum, peak_idx):
    """找收获期: 峰值后NDVI加速下降点"""
    n = len(values)
    if peak_idx >= n - 3:
        return n - 1
    # 峰值后部分
    post_peak = values[peak_idx:]
    post_cusum = cusum[peak_idx:]
    # 找CUSUM从升转降的拐点
    for i in range(1, len(post_cusum) - 1):
        if post_cusum[i] > post_cusum[i - 1] and post_cusum[i] > post_cusum[i + 1]:
            return peak_idx + i
    # 找不到就找NDVI下降到峰值60%的点
    for i in range(len(post_peak)):
        if post_peak[i] < values[peak_idx] * 0.6:
            return peak_idx + i
    return n - 1


def get_growth_stage_summary(phenology: dict, current_ndvi: float) -> str:
    """根据当前NDVI和物候期，返回文字总结"""
    if "error" in phenology:
        return "物候数据不足，无法判断"

    stages = ["返青期", "拔节期", "抽穗期", "成熟期", "收获期"]
    descriptions = {
        "返青期": "作物返青，根系开始活跃，适宜追施返青肥。",
        "拔节期": "快速生长阶段，需水量大，注意灌溉和追肥。",
        "抽穗期": "生殖生长关键期，对水分和养分敏感，避免干旱。",
        "成熟期": "灌浆成熟，适当控水，准备收获。",
        "收获期": "适宜收获，建议关注天气预报，避开雨天作业。",
    }

    # 找当前NDVI最接近的物候期
    for stage in stages:
        if stage in phenology:
            stage_ndvi = phenology[stage]["ndvi"]
            if abs(current_ndvi - stage_ndvi) < 0.1:
                return descriptions.get(stage, f"当前处于{stage}")

    if current_ndvi < 0.2:
        return "当前植被覆盖低，可能处于休耕或刚播种阶段。"
    elif current_ndvi > 0.7:
        return "植被覆盖度高，作物处于旺盛生长期。"
    return "作物处于正常生长阶段。"
