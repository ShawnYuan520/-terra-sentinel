"""农机型号"""
import uuid
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Machinery(Base):
    __tablename__ = "machinery"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(100), comment="整地机械/收获机械/植保机械/耕作机械/播种机械")
    description: Mapped[str | None] = mapped_column(Text)
    specs: Mapped[str | None] = mapped_column(Text, comment="JSON格式规格参数")
    suitable_for: Mapped[str | None] = mapped_column(String(500))
    accent: Mapped[str | None] = mapped_column(String(20), comment="主题色")
    image_type: Mapped[str | None] = mapped_column(String(50))
