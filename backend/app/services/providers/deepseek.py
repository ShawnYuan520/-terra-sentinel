"""DeepSeek Provider — 兼容 OpenAI SDK"""
from openai import AsyncOpenAI
from app.services.providers.base import AIProvider


class DeepSeekProvider(AIProvider):
    BASE_URL = "https://api.deepseek.com/v1"

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self._model = model
        self._client = AsyncOpenAI(api_key=api_key, base_url=self.BASE_URL)

    @property
    def model_name(self) -> str:
        return self._model

    async def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        kwargs = {"model": self._model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        resp = await self._client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message
        tool_calls = None
        if msg.tool_calls:
            tool_calls = [
                {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]
        return {
            "content": msg.content or "",
            "tool_calls": tool_calls,
            "model": resp.model,
            "tokens_in": resp.usage.prompt_tokens if resp.usage else 0,
            "tokens_out": resp.usage.completion_tokens if resp.usage else 0,
        }

    async def stream_chat(self, messages: list[dict], tools: list[dict] | None = None):
        kwargs = {"model": self._model, "messages": messages, "stream": True}
        if tools:
            kwargs["tools"] = tools

        stream = await self._client.chat.completions.create(**kwargs)
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
