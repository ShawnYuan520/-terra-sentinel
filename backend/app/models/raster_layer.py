"""栅格图层元数据"""
import uuid
from sqlalchemy import String, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class RasterLayer(Base):
    __tablename__ = "raster_layers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    crs: Mapped[str | None] = mapped_column(String(100))
    resolution: Mapped[str | None] = mapped_column(String(100))
    bounds_left: Mapped[float | None] = mapped_column(Float)
    bounds_bottom: Mapped[float | None] = mapped_column(Float)
    bounds_right: Mapped[float | None] = mapped_column(Float)
    bounds_top: Mapped[float | None] = mapped_column(Float)
    min_value: Mapped[float | None] = mapped_column(Float)
    max_value: Mapped[float | None] = mapped_column(Float)
    mean_value: Mapped[float | None] = mapped_column(Float)
