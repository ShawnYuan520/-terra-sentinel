"""腐解剂类型"""
import uuid
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class DecomposerType(Base):
    __tablename__ = "decomposer_types"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    suitable_crops: Mapped[str | None] = mapped_column(String(500))
    suitable_soil: Mapped[str | None] = mapped_column(String(500))
    usage_guide: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    features: Mapped[str | None] = mapped_column(Text)