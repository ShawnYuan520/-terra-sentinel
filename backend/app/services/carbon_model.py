"""
SOC 周转碳汇预测模型
基于 RothC 简化框架 + 张丹丹(2024)东北农田有机碳矿化实测参数
核心: k_base = 0.0485 (黑土年矿化率 4.85%)
"""
import math
from datetime import datetime


# ── 东北不同土壤类型矿化参数 (张丹丹 2024, 表3-2) ──
SOIL_MINERALIZATION = {
    "黑土":    {"rate": 0.0485, "cum_g_kg": 2.50},  # 矿化率最低, 最稳定
    "草甸土":  {"rate": 0.0487, "cum_g_kg": 2.66},
    "白浆土":  {"rate": 0.0490, "cum_g_kg": 2.68},
    "暗棕壤":  {"rate": 0.0679, "cum_g_kg": 2.82},
    "冲积土":  {"rate": 0.0731, "cum_g_kg": 1.58},
    "风沙土":  {"rate": 0.1106, "cum_g_kg": 3.12},  # 矿化最快
}


def predict_carbon_dynamics(
    soc_current: float,
    straw_input: float,
    temperature_c: float,
    moisture_pct: float,
    clay_pct: float = 20,
    area_mu: float = 100,
    years: int = 5,
    soil_type: str = "黑土",
) -> dict:
    """
    秸秆还田下 SOC 和碳汇变化预测

    核心方程:
    SOC(t+1) = SOC(t) + I_input × e − SOC(t) × k × f_T × f_W × f_C

    参数来源:
    - k_base: 张丹丹(2024) 东北农田SOC矿化率实测
    - e_eff:  IPCC(2019) 秸秆还田碳转化效率
    - f_T:    RothC Arrhenius温度修正
    - f_W:    水分修正 (60%田间持水量最优)
    - f_C:    粘粒保护 (物理保护作用)
    """
    BD = 1.30           # g/cm³ — 东北黑土典型容重
    depth = 20           # cm — 耕层深度
    e_eff = 0.15         # 秸秆碳转化效率 (RothC)

    # 根据土壤类型选择矿化率
    soil_params = SOIL_MINERALIZATION.get(soil_type, SOIL_MINERALIZATION["黑土"])
    k_base = soil_params["rate"]

    # 修正因子
    f_T = _temp_modifier(temperature_c)
    f_W = _moisture_modifier(moisture_pct)
    f_C = _clay_modifier(clay_pct)

    k_eff = k_base * f_T * f_W * f_C

    # 秸秆碳输入
    carbon_input_per_mu = straw_input * 0.44
    mu_to_m2 = 666.67
    soil_mass_per_mu = BD * depth * 0.01 * mu_to_m2 * 1000
    soc_increment = carbon_input_per_mu / soil_mass_per_mu * 1000

    # 逐年模拟
    soc_series = [soc_current]
    carbon_seq_series = []
    total_carbon_seq = 0.0
    current_year = datetime.now().year

    for year in range(years):
        soc_t = soc_series[-1]
        soc_loss = soc_t * k_eff
        soc_new = soc_t + soc_increment * e_eff - soc_loss
        soc_new = max(5, min(60, soc_new))
        soc_series.append(round(soc_new, 2))

        delta_soc = soc_new - soc_t
        delta_carbon = delta_soc * soil_mass_per_mu / 1000
        delta_co2e = delta_carbon * 3.67 / 1000
        carbon_seq_series.append({
            "year": current_year + year,
            "soc_start": round(soc_t, 2),
            "soc_end": round(soc_new, 2),
            "delta_soc": round(delta_soc, 2),
            "carbon_seq_tco2e": round(delta_co2e, 3),
        })
        total_carbon_seq += delta_co2e

    return {
        "model": "RothC简化版 (基于张丹丹2024实测参数)",
        "soil_type": soil_type,
        "k_base": k_base,
        "reference": "张丹丹.模拟增温对农田土壤有机碳矿化及腐殖质组成的影响[D].2024.",
        "parameters": {
            "k_effective": round(k_eff, 5),
            "temp_modifier": round(f_T, 3),
            "moisture_modifier": round(f_W, 3),
            "clay_modifier": round(f_C, 3),
            "soc_increment_per_year": round(soc_increment, 3),
        },
        "soc_trajectory": soc_series,
        "yearly_detail": carbon_seq_series,
        "total_carbon_seq_tco2e": round(total_carbon_seq, 2),
        "soc_change": round(soc_series[-1] - soc_series[0], 2),
        "annual_avg_seq": round(total_carbon_seq / max(1, years), 2),
        "recommendation": _make_recommendation(soc_current, straw_input, k_eff, soc_series[-1] - soc_series[0]),
    }


def _temp_modifier(T):
    """Arrhenius温度修正 (RothC标准)"""
    if T is None:
        T = 15
    return 47.9 / (1 + math.exp(106 / (T + 18.3))) / 100


def _moisture_modifier(W):
    """水分修正 — 60%田间持水量最优"""
    if W is None:
        W = 60
    x = W / 60
    if x <= 0.5:
        return 0.2
    return min(1.0, 0.2 + 0.8 * (x - 0.2))


def _clay_modifier(clay_pct):
    """粘粒保护因子 — 粘粒含量越高, 矿化越慢"""
    return 1 - 0.75 * (clay_pct / 100)


def _make_recommendation(soc, straw, k, delta):
    if delta > 2:
        return "SOC持续提升，碳汇潜力大。建议保持当前秸秆还田量。"
    elif delta > 0:
        return f"SOC缓慢提升(+{delta:.1f}g/kg)。可适当增秸秆还田至{straw*1.3:.0f}kg/亩。"
    elif delta > -1:
        return f"SOC基本持平。矿化速率k={k:.3f}，建议增施有机肥+秸秆还田。"
    else:
        return f"SOC下降({delta:.1f}g/kg)。矿化过快(k={k:.3f})。增秸秆+减耕+有机肥。"

