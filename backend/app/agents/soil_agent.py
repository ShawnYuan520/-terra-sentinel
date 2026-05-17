"""土壤分析 Agent"""
from app.agents.tools import register_tool
from app.services.soil import SoilService


@register_tool("analyze_soil")
async def analyze_soil(db, field_id: str) -> dict:
    """分析土壤数据并给出建议"""
    from app.prompts import load_prompt
    from sqlalchemy import select
    from app.models.field import Field
    from app.models.decomposer_type import DecomposerType

    svc = SoilService(db)

    record = await svc.get_latest_record(field_id)
    if not record:
        return {"field_id": field_id, "analysis": "暂无该地块的土壤检测数据"}

    recommendation = await svc.recommend_decomposer(field_id)
    field = (await db.execute(select(Field).where(Field.id == field_id))).scalar_one_or_none()

    decomposers = (await db.execute(select(DecomposerType))).scalars().all()
    decomposer_list = "\n".join(f"- {d.name}: {d.description or ''}" for d in decomposers)

    analysis_template = load_prompt("soil_analysis",
        field_name=field.name if field else "未知",
        ph=record.ph or "未检测",
        organic_matter=record.organic_matter or "未检测",
        nitrogen=record.nitrogen or "未检测",
        phosphorus=record.phosphorus or "未检测",
        potassium=record.potassium or "未检测",
        moisture=record.moisture or "未检测",
        decomposer_list=decomposer_list,
    )

    assessments = []
    if record.ph is not None:
        if record.ph < 5.5:
            assessments.append("土壤偏酸，建议施用石灰调节")
        elif record.ph > 8.0:
            assessments.append("土壤偏碱，建议施用硫磺或有机肥调节")
        else:
            assessments.append(f"土壤 pH {record.ph} 正常")
    if record.organic_matter is not None:
        if record.organic_matter < 10:
            assessments.append(f"有机质含量 ({record.organic_matter}g/kg) 偏低，需增施有机肥")
        elif record.organic_matter > 30:
            assessments.append(f"有机质含量 ({record.organic_matter}g/kg) 丰富")
        else:
            assessments.append(f"有机质含量 ({record.organic_matter}g/kg) 适中")

    return {
        "field_id": field_id,
        "field_name": field.name if field else "未知",
        "record_date": record.record_date.isoformat(),
        "soil_data": {
            "ph": record.ph,
            "organic_matter_g_per_kg": record.organic_matter,
            "nitrogen_g_per_kg": record.nitrogen,
            "phosphorus_mg_per_kg": record.phosphorus,
            "potassium_mg_per_kg": record.potassium,
            "moisture_pct": record.moisture,
        },
        "assessments": assessments,
        "recommended_decomposer": recommendation.decomposer_name,
        "recommendation_reason": recommendation.reason,
        "analysis_instructions": analysis_template,
    }
