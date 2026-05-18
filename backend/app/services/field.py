"""田块服务"""
import json
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.field import Field
from app.schemas.field import FieldCreate


class FieldService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_field(self, user_id: str, data: FieldCreate) -> Field:
        geom_json = json.dumps(data.geojson.model_dump())
        field = Field(user_id=user_id, name=data.name, geom=geom_json,
                      area_ha=data.area_ha, crop_type=data.crop_type)
        self.db.add(field)
        await self.db.flush()
        return field

    async def get_fields_by_user(self, user_id: str, offset: int = 0, limit: int = 20):
        q = select(Field).where(Field.user_id == user_id).offset(offset).limit(limit)
        result = await self.db.execute(q)
        items = list(result.scalars().all())
        cq = select(func.count()).select_from(Field).where(Field.user_id == user_id)
        total = (await self.db.execute(cq)).scalar()
        return total, items

    async def get_all_fields(self, offset: int = 0, limit: int = 20):
        q = select(Field).offset(offset).limit(limit)
        result = await self.db.execute(q)
        items = list(result.scalars().all())
        total = (await self.db.execute(select(func.count()).select_from(Field))).scalar()
        return total, items
