from pydantic import BaseModel
from datetime import datetime


class GeoJSONGeometry(BaseModel):
    type: str = "Polygon"
    coordinates: list[list[list[float]]]


class FieldCreate(BaseModel):
    name: str
    geojson: GeoJSONGeometry
    area_ha: float | None = None
    crop_type: str | None = None


class FieldOut(BaseModel):
    id: str
    user_id: str
    name: str
    geom: str | None = None
    area_ha: float | None
    crop_type: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FieldUpdate(BaseModel):
    name: str | None = None
    crop_type: str | None = None
    area_ha: float | None = None


class FieldListOut(BaseModel):
    total: int
    items: list[FieldOut]