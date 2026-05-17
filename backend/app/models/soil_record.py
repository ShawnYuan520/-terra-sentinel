"""土壤检测记录"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class SoilRecord(Base):
    __tablename__ = "soil_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    field_id: Mapped[str] = mapped_column(String(36), ForeignKey("fields.id"), nullable=False)
    ph: Mapped[float | None] = mapped_column(Float)
    organic_matter: Mapped[float | None] = mapped_column(Float)
    nitrogen: Mapped[float | None] = mapped_column(Float)
    phosphorus: Mapped[float | None] = mapped_column(Float)
    potassium: Mapped[float | None] = mapped_column(Float)
    moisture: Mapped[float | None] = mapped_column(Float)
    recommended_decomposer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("decomposer_types.id"), nullable=True
    )
    record_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )