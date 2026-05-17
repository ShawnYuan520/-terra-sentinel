"""AI Provider 抽象基类"""
from abc import ABC, abstractmethod


class AIProvider(ABC):
    """统一 AI Provider 接口"""

    @abstractmethod
    async def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """发送对话请求，返回 {"content", "tool_calls", "model", "tokens_in", "tokens_out"}"""
        ...

    @abstractmethod
    async def stream_chat(self, messages: list[dict], tools: list[dict] | None = None):
        """流式对话 — 异步生成器，yield 文本片段"""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...
