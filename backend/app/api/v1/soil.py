from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user
from app.services.soil import SoilService
from app.schemas.soil import SoilRecordCreate, SoilRecordOut, SoilRecommendOut

router = APIRouter(prefix="/soil", tags=["土壤分析"])


@router.post("/records", response_model=SoilRecordOut)
async def create_record(
    data: SoilRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    svc = SoilService(db)
    return await svc.create_record(data)


@router.get("/records/{field_id}", response_model=list[SoilRecordOut])
async def list_records(
    field_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user),
):
    svc = SoilService(db)
    _, items = await svc.get_records_by_field(field_id, offset, limit)
    return items


@router.post("/recommend/{field_id}", response_model=SoilRecommendOut)
async def recommend_decomposer(
    field_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    svc = SoilService(db)
    return await svc.recommend_decomposer(field_id)