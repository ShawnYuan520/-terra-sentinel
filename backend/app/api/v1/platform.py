"""平台统计 API"""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_optional_user
from app.models.user import User
from app.models.field import Field
from app.models.carbon_report import CarbonReport
from app.models.soil_record import SoilRecord
from app.models.knowledge_article import KnowledgeArticle

router = APIRouter(prefix="/platform", tags=["平台"])


@router.get("/stats")
async def platform_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user),
):
    user_count = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    field_count = (await db.execute(select(func.count()).select_from(Field))).scalar() or 0
    carbon_result = await db.execute(
        select(func.coalesce(func.sum(CarbonReport.carbon_amount), 0)).select_from(CarbonReport)
    )
    total_carbon = round(float(carbon_result.scalar() or 0), 1)
    article_count = (await db.execute(select(func.count()).select_from(KnowledgeArticle))).scalar() or 0
    soil_count = (await db.execute(select(func.count()).select_from(SoilRecord))).scalar() or 0

    # 当前用户自己的统计（未登录时返回 0）
    my_field_count = 0
    my_carbon = 0.0
    if current_user:
        my_field_count = (await db.execute(
            select(func.count()).select_from(Field).where(Field.user_id == current_user["sub"])
        )).scalar() or 0
        my_carbon_result = await db.execute(
            select(func.coalesce(func.sum(CarbonReport.carbon_amount), 0))
            .select_from(CarbonReport)
            .where(CarbonReport.user_id == current_user["sub"])
        )
        my_carbon = round(float(my_carbon_result.scalar() or 0), 1)

    return {
        "total_users": int(user_count),
        "total_fields": int(field_count),
        "total_carbon_tco2e": total_carbon,
        "total_articles": int(article_count),
        "total_soil_records": int(soil_count),
        "my_fields": int(my_field_count),
        "my_carbon_tco2e": my_carbon,
        "today_operation_mu": int(my_field_count * 15 * 3.5),
        "machinery_online": min(12, int(field_count * 2)),
    }
