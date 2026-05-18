from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user
from app.services.field import FieldService
from app.models.field import Field
from app.schemas.field import FieldCreate, FieldOut, FieldListOut, FieldUpdate

router = APIRouter(prefix="/fields", tags=["田块"])


@router.post("", response_model=FieldOut)
async def create_field(
    data: FieldCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    svc = FieldService(db)
    field = await svc.create_field(current_user["sub"], data)
    return field


@router.get("", response_model=FieldListOut)
async def list_fields(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user),
):
    svc = FieldService(db)
    if current_user:
        total, items = await svc.get_fields_by_user(current_user["sub"], offset, limit)
    else:
        total, items = await svc.get_all_fields(offset, limit)
    return FieldListOut(total=total, items=items)


@router.get("/{field_id}", response_model=FieldOut)
async def get_field(
    field_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user),
):
    q = select(Field).where(Field.id == field_id)
    if current_user:
        q = q.where(Field.user_id == current_user["sub"])
    result = await db.execute(q)
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(404, "田块不存在")
    return field


@router.put("/{field_id}", response_model=FieldOut)
async def update_field(
    field_id: str,
    data: FieldUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Field).where(Field.id == field_id, Field.user_id == current_user["sub"])
    )
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(404, "田块不存在")

    if data.name is not None:
        field.name = data.name
    if data.crop_type is not None:
        field.crop_type = data.crop_type
    if data.area_ha is not None:
        field.area_ha = data.area_ha

    await db.flush()
    return field


@router.delete("/{field_id}")
async def delete_field(
    field_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Field).where(Field.id == field_id, Field.user_id == current_user["sub"]))
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(404, "田块不存在")

    # 级联删除关联数据
    from app.models.soil_record import SoilRecord
    from app.models.carbon_report import CarbonReport
    from app.models.remote_sensing_ts import RemoteSensingTimeseries
    from app.models.ai_agent_log import AIAgentLog

    await db.execute(delete(SoilRecord).where(SoilRecord.field_id == field_id))
    await db.execute(delete(CarbonReport).where(CarbonReport.field_id == field_id))
    await db.execute(delete(RemoteSensingTimeseries).where(RemoteSensingTimeseries.field_id == field_id))
    await db.execute(delete(AIAgentLog).where(AIAgentLog.field_id == field_id))
    await db.delete(field)
    return {"ok": True}