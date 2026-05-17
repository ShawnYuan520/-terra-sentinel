"""
AHP (层次分析法) + 熵权法 + TOPSIS 耕地质量综合评价
参考: GB/T 33469-2016 耕地质量等级, 东北黑土区耕地质量评价指标
"""
import math
import numpy as np


# ── AHP 主观权重 ──
# 基于张超(2024) 东北黑土区 SHAP 分析 + 专家打分
# 关键指标排序: 有机质(SOC) > pH > 粘粒 > 有效养分
# 论文结果: SHAP-MDS R²=0.47, 非线性评分优于线性(R²=0.48 vs 0.26)
AHP_WEIGHTS = {
    "soc": 0.25,         # 土壤有机碳 — SHAP 最重要特征
    "ndvi_peak": 0.18,   # NDVI峰值 — 产量相关性强
    "slope": 0.16,       # 坡度 — 机械化可行性
    "ph": 0.15,          # pH — 养分有效性 (SHAP 第二重要)
    "clay": 0.08,        # 粘粒 — 保水保肥 (SHAP 核心指标)
    "texture_score": 0.08,  # 质地综合
    "dem": 0.05,         # 海拔
    "soil_moisture": 0.05,  # 水分
}


def _normalize_ph(ph):
    """pH归一化: 6.5最优，偏离越大越差"""
    if ph is None:
        return 0.5
    return max(0, 1 - abs(ph - 6.5) / 4)


def _normalize_soc(soc):
    """SOC归一化: 0-40g/kg映射到0-1"""
    if soc is None:
        return 0.3
    return min(1, max(0, soc / 35))


def _normalize_slope(slope):
    """坡度归一化: 0°最优，25°以上不可用"""
    if slope is None:
        return 0.7
    return max(0, 1 - slope / 25)


def _normalize_texture(texture_name):
    """质地评分: 壤土最优"""
    if not texture_name:
        return 0.6
    scores = {"壤土": 1.0, "粉壤土": 0.9, "砂壤土": 0.75,
              "黏壤土": 0.7, "粉黏土": 0.6, "砂土": 0.4, "黏土": 0.5}
    return scores.get(texture_name, 0.6)


def _normalize_dem(dem, base=200):
    """海拔归一化: 以200m为基准，越低越好(积温高)"""
    if dem is None:
        return 0.7
    return max(0, 1 - max(0, dem - base) / 800)


def _normalize_moisture(moisture_pct):
    """土壤水分: 60%最优"""
    if moisture_pct is None:
        return 0.5
    return max(0, 1 - abs(moisture_pct - 60) / 60)


def entropy_weight(matrix: np.ndarray) -> np.ndarray:
    """
    熵权法 — 客观权重
    数据变异越大 → 信息熵越小 → 权重越大
    """
    n, m = matrix.shape  # n个样本, m个指标
    # 归一化
    p = matrix / (matrix.sum(axis=0) + 1e-10)
    # 信息熵
    e = -np.sum(p * np.log(p + 1e-10), axis=0) / math.log(n + 1e-10)
    e = np.nan_to_num(e, nan=1.0)
    # 冗余度 → 权重
    d = 1 - e
    w = d / (d.sum() + 1e-10)
    return w


def evaluate_field(soil: dict, ndvi_peak: float = None, moisture: float = None) -> dict:
    """
    单地块综合评价: AHP主观权重 + TOPSIS排序

    输入:
    - soil: 土壤剖面数据 {soc, ph, slope, dem, texture_name, sand, silt, clay}
    - ndvi_peak: NDVI峰值 (0-1)
    - moisture: 土壤水分百分位 (0-100)

    输出: {score, grade, strengths, weaknesses, details}
    """
    def _normalize_clay(clay_pct):
        """粘粒含量归一化: 20-30%最优"""
        if clay_pct is None:
            return 0.6
        if 20 <= clay_pct <= 35:
            return 1.0
        return max(0, 1 - abs(clay_pct - 27.5) / 30)

    # 指标归一化
    metrics = {
        "soc": _normalize_soc(soil.get("soc")),
        "ndvi_peak": ndvi_peak if ndvi_peak is not None else 0.5,
        "slope": _normalize_slope(soil.get("slope")),
        "ph": _normalize_ph(soil.get("ph")),
        "clay": _normalize_clay(soil.get("clay")),
        "texture_score": _normalize_texture(soil.get("texture_name")),
        "dem": _normalize_dem(soil.get("dem")),
        "soil_moisture": _normalize_moisture(moisture),
    }

    # AHP加权总分
    total_score = sum(metrics[k] * AHP_WEIGHTS[k] for k in AHP_WEIGHTS) * 100

    # 等级划分 (参考国标)
    if total_score >= 85:
        grade = "一等 · 优质耕地"
    elif total_score >= 70:
        grade = "二等 · 良好耕地"
    elif total_score >= 55:
        grade = "三等 · 中等耕地"
    elif total_score >= 40:
        grade = "四等 · 一般耕地"
    else:
        grade = "五等 · 低产耕地"

    # 优势与劣势
    strengths = []
    weaknesses = []
    thresholds = {"soc": 0.7, "ndvi_peak": 0.65, "slope": 0.8, "ph": 0.7,
                  "clay": 0.6, "texture_score": 0.7, "dem": 0.7, "soil_moisture": 0.6}
    labels = {"soc": "有机碳含量高", "ndvi_peak": "植被长势好", "slope": "地势平坦",
              "ph": "酸碱度适宜", "clay": "粘粒含量适中", "texture_score": "土壤质地好",
              "dem": "海拔适中", "soil_moisture": "墒情适宜"}

    for k in AHP_WEIGHTS:
        if metrics[k] >= thresholds[k]:
            strengths.append(labels[k])
        elif metrics[k] < 0.4:
            weaknesses.append(labels[k].replace("高", "偏低").replace("好", "偏差")
                              .replace("适宜", "偏低").replace("平坦", "偏陡")
                              .replace("适中", "偏高"))

    return {
        "score": round(total_score, 1),
        "grade": grade,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "details": {k: round(v, 3) for k, v in metrics.items()},
        "weights": AHP_WEIGHTS,
        "_meta": "AHP层次分析法 + 熵权修正",
    }


def batch_evaluate(fields_data: list[dict]) -> list[dict]:
    """
    多地块批量评价 — 熵权修正 + TOPSIS排序
    fields_data: [{field_id, soc, ndvi_peak, slope, ph, texture_name, dem, moisture}, ...]
    """
    if len(fields_data) < 2:
        return [evaluate_field(f) for f in fields_data]

    # 构建评价矩阵
    indicators = list(AHP_WEIGHTS.keys())
    matrix = np.zeros((len(fields_data), len(indicators)))
    for i, f in enumerate(fields_data):
        metrics = {
            "soc": _normalize_soc(f.get("soc")),
            "ndvi_peak": f.get("ndvi_peak", 0.5),
            "slope": _normalize_slope(f.get("slope")),
            "ph": _normalize_ph(f.get("ph")),
            "texture_score": _normalize_texture(f.get("texture_name")),
            "dem": _normalize_dem(f.get("dem")),
            "soil_moisture": _normalize_moisture(f.get("moisture")),
        }
        for j, k in enumerate(indicators):
            matrix[i, j] = metrics[k]

    # 熵权
    e_weights = entropy_weight(matrix)

    # 组合权重 (AHP 70% + 熵权 30%)
    combined = {}
    for j, k in enumerate(indicators):
        combined[k] = AHP_WEIGHTS[k] * 0.7 + e_weights[j] * 0.3

    # TOPSIS 综合排序
    norm = matrix / np.sqrt((matrix ** 2).sum(axis=0) + 1e-10)
    weighted = norm * np.array([combined[k] for k in indicators])
    ideal_best = weighted.max(axis=0)
    ideal_worst = weighted.min(axis=0)
    d_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    d_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))
    topsis_scores = d_worst / (d_best + d_worst + 1e-10)

    results = []
    for i, f in enumerate(fields_data):
        result = evaluate_field(f, f.get("ndvi_peak"), f.get("moisture"))
        result["topsis_score"] = round(float(topsis_scores[i]), 3)
        result["topsis_rank"] = i + 1
        result["combined_weights"] = {k: round(float(v), 3) for k, v in combined.items()}
        results.append(result)

    # 按TOPSIS排序
    results.sort(key=lambda x: x["topsis_score"], reverse=True)
    for i, r in enumerate(results):
        r["topsis_rank"] = i + 1

    return results
