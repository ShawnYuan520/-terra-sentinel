from pydantic import BaseModel
from datetime import datetime


class SoilRecordCreate(BaseModel):
    field_id: str
    ph: float | None = None
    organic_matter: float | None = None
    nitrogen: float | None = None
    phosphorus: float | None = None
    potassium: float | None = None
    moisture: float | None = None


class SoilRecordOut(BaseModel):
    id: str
    field_id: str
    ph: float | None
    organic_matter: float | None
    nitrogen: float | None
    phosphorus: float | None
    potassium: float | None
    moisture: float | None
    recommended_decomposer_id: str | None
    record_date: datetime

    model_config = {"from_attributes": True}


class SoilRecommendOut(BaseModel):
    soil_record_id: str
    decomposer_id: str | None
    decomposer_name: str | None
    reason: str