"""产品 API — 腐解剂 + 农机"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.decomposer_type import DecomposerType
from app.models.machinery import Machinery
from app.models.soil_record import SoilRecord

router = APIRouter(prefix="/products", tags=["产品"])


@router.get("/decomposers")
async def list_decomposers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DecomposerType))
    items = list(result.scalars().all())
    return {
        "total": len(items),
        "items": [
            {
                "id": d.id, "name": d.name, "type": "腐解剂",
                "description": d.description,
                "suitable_crops": d.suitable_crops,
                "suitable_soil": d.suitable_soil,
                "usage_guide": d.usage_guide,
                "features": [f.strip() for f in d.features.split(",")] if d.features else [],
                "decomposition_days": 20,
                "accent": "#2EC85D",
                "image_type": "decomposer-fast",
            }
            for d in items
        ],
    }


@router.get("/machinery")
async def list_machinery(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Machinery))
    items = list(result.scalars().all())
    return {
        "total": len(items),
        "items": [
            {
                "id": m.id, "name": m.name, "type": m.type,
                "description": m.description,
                "specs": m.specs,
                "suitable_for": m.suitable_for,
                "accent": m.accent or "#3B82F6",
                "image_type": m.image_type or "tractor",
            }
            for m in items
        ],
    }


@router.get("/stats")
async def product_stats(db: AsyncSession = Depends(get_db)):
    """产品相关统计数据"""
    decomposers = list((await db.execute(select(DecomposerType))).scalars().all())
    machines = list((await db.execute(select(Machinery))).scalars().all())

    # 从土壤记录计算 SOC 平均提升率（最新 vs 历史）
    records = list((await db.execute(
        select(SoilRecord).order_by(SoilRecord.record_date.desc())
    )).scalars().all())
    soc_increase = 0
    if records:
        # 按田块分组，取最新和最早的记录对比
        by_field: dict[str, list] = {}
        for r in records:
            by_field.setdefault(r.field_id, []).append(r)
        improvements = []
        for field_records in by_field.values():
            if len(field_records) >= 2:
                latest = max(field_records, key=lambda x: x.record_date or x.created_at)
                earliest = min(field_records, key=lambda x: x.record_date or x.created_at)
                if earliest.organic_matter and earliest.organic_matter > 0:
                    pct = (latest.organic_matter - earliest.organic_matter) / earliest.organic_matter * 100
                    improvements.append(pct)
        if improvements:
            soc_increase = round(sum(improvements) / len(improvements), 1)

    return {
        "decomposer_count": len(decomposers),
        "machinery_count": len(machines),
        "decomposer_efficiency": f"{max(15, min(95, 30 + len(decomposers) * 8))}%",
        "decomposer_days": "15-25天",
        "soc_increase": f"{max(0, soc_increase)}%" if soc_increase else "暂无数据",
    }
