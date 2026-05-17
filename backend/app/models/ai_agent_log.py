"""AI Agent 调用日志 – 调试/评估/成本控制"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AIAgentLog(Base):
    __tablename__ = "ai_agent_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    field_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("fields.id"), nullable=True)
    agent_type: Mapped[str] = mapped_column(String(50), comment="soil/carbon/weather/general")
    prompt: Mapped[str] = mapped_column(Text, comment="用户输入")
    tool_calls: Mapped[str | None] = mapped_column(Text, comment="JSON: 调用了哪些工具")
    response: Mapped[str | None] = mapped_column(Text, comment="AI 回复")
    model: Mapped[str | None] = mapped_column(String(50), comment="使用的模型")
    tokens_in: Mapped[int | None] = mapped_column(Integer)
    tokens_out: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer, comment="响应延迟 毫秒")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )