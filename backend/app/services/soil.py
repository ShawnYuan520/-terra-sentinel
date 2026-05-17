"""土壤分析 + 腐解剂推荐"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.soil_record import SoilRecord
from app.models.decomposer_type import DecomposerType
from app.schemas.soil import SoilRecordCreate, SoilRecommendOut


class SoilService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_record(self, data: SoilRecordCreate) -> SoilRecord:
        record = SoilRecord(**data.model_dump())
        self.db.add(record)
        await self.db.flush()
        return record

    async def get_records_by_field(self, field_id: str, offset: int = 0, limit: int = 20):
        q = select(SoilRecord).where(SoilRecord.field_id == field_id).order_by(SoilRecord.record_date.desc()).offset(offset).limit(limit)
        result = await self.db.execute(q)
        items = list(result.scalars().all())
        cq = select(func.count()).select_from(SoilRecord).where(SoilRecord.field_id == field_id)
        total = (await self.db.execute(cq)).scalar()
        return total, items

    async def get_latest_record(self, field_id: str) -> SoilRecord | None:
        q = select(SoilRecord).where(SoilRecord.field_id == field_id).order_by(SoilRecord.record_date.desc()).limit(1)
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def recommend_decomposer(self, field_id: str) -> SoilRecommendOut:
        record = await self.get_latest_record(field_id)
        if not record:
            return SoilRecommendOut(soil_record_id="", decomposer_id=None, decomposer_name=None, reason="暂无土壤数据")

        result = await self.db.execute(select(DecomposerType))
        all_decomposers = list(result.scalars().all())
        if not all_decomposers:
            return SoilRecommendOut(soil_record_id=str(record.id), decomposer_id=None, decomposer_name=None, reason="腐解剂库为空")

        # 获取田块作物类型
        crop_type = None
        from app.models.field import Field
        f = (await self.db.execute(select(Field).where(Field.id == record.field_id))).scalar_one_or_none()
        if f:
            crop_type = f.crop_type

        # 根据有机质和作物匹配腐解剂
        om = record.organic_matter or 20
        best = all_decomposers[0]
        reason = "默认推荐"
        for d in all_decomposers:
            name = (d.name or "").lower()
            if om < 10 and "高活性" in name:
                best = d; reason = "有机质偏低，推荐高活性腐解剂加速腐解"; break
            elif om > 30 and ("温和" in name or "标准" in name):
                best = d; reason = "有机质含量高，推荐温和型腐解剂维持养分平衡"; break

        # 进一步按作物筛选
        if crop_type and not any(kw in (best.name or "").lower() for kw in ["高活性", "温和"]):
            for d in all_decomposers:
                if crop_type in (d.suitable_crops or ""):
                    best = d; reason = f"基于作物类型 {crop_type} 推荐 {d.name}"; break

        record.recommended_decomposer_id = best.id
        await self.db.flush()

        return SoilRecommendOut(
            soil_record_id=str(record.id), decomposer_id=best.id,
            decomposer_name=best.name, reason=reason,
        )
