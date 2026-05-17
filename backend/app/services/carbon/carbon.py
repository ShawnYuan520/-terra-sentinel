"""碳汇计算引擎"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.carbon_report import CarbonReport
from app.schemas.carbon import CarbonReportCreate

CARBON_CONVERSION_FACTOR = 0.4  # tCO2e / 吨秸秆


class CarbonService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_report(self, user_id: str, data: CarbonReportCreate) -> CarbonReport:
        carbon_amount = data.straw_amount * CARBON_CONVERSION_FACTOR
        report = CarbonReport(
            user_id=user_id, field_id=data.field_id,
            period_start=data.period_start, period_end=data.period_end,
            straw_amount=data.straw_amount, carbon_amount=round(carbon_amount, 2),
            status="generated",
        )
        self.db.add(report)
        await self.db.flush()
        return report

    async def get_reports_by_user(self, user_id: str, offset: int = 0, limit: int = 20):
        q = select(CarbonReport).where(CarbonReport.user_id == user_id).offset(offset).limit(limit).order_by(CarbonReport.created_at.desc())
        result = await self.db.execute(q)
        items = list(result.scalars().all())
        cq = select(func.count()).select_from(CarbonReport).where(CarbonReport.user_id == user_id)
        total = (await self.db.execute(cq)).scalar()
        return total, items
