"""Agent Router — DeepSeek LLM + tool calling，无 API Key 时降级为规则引擎"""
import json
import app.agents.soil_agent   # noqa: F401 注册工具
import app.agents.carbon_agent  # noqa: F401
import app.agents.weather_agent  # noqa: F401
from app.agents.tools import _tool_executors, execute_tool, SYSTEM_PROMPT, TOOL_SCHEMAS
from app.services.providers.router import get_provider


class AgentRouter:
    """AI Agent — LLM 优先，规则引擎降级"""

    async def chat(self, user_message: str, field_id: str | None, db, current_user: dict = None) -> str:
        provider = get_provider()

        # 无 Provider 时降级为规则引擎
        if provider is None:
            return await self._rule_based(user_message, field_id, db)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        # Step 1: LLM 决定是否需要调用工具
        resp = await provider.chat(messages, tools=TOOL_SCHEMAS)

        if resp.get("tool_calls"):
            messages.append({
                "role": "assistant",
                "content": resp.get("content") or "",
                "tool_calls": resp["tool_calls"],
            })

            # Step 2: 执行工具
            for tc in resp["tool_calls"]:
                fn = tc["function"]
                tool_name = fn["name"]
                try:
                    args = json.loads(fn["arguments"])
                except json.JSONDecodeError:
                    args = {}
                # 前端/上下文传入的 field_id 始终覆盖 LLM 的值
                if field_id:
                    args["field_id"] = field_id
                tool_result = await execute_tool(tool_name, args, db)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(tool_result, ensure_ascii=False, default=str),
                })

            # Step 3: LLM 生成最终回复
            final = await provider.chat(messages)
            reply = final.get("content") or "抱歉，无法处理您的请求"
            await self._log(user_message, field_id, db, current_user, reply, resp)
            return reply

        reply = resp.get("content") or "抱歉，无法处理您的请求"
        await self._log(user_message, field_id, db, current_user, reply, resp)
        return reply

    async def stream_chat(self, user_message: str, field_id: str | None, db, current_user: dict = None):
        """流式对话 — 异步生成器，yield 文本片段"""
        provider = get_provider()

        if provider is None:
            text = await self._rule_based(user_message, field_id, db)
            yield text
            return

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        # 非流式判断是否需要工具调用
        resp = await provider.chat(messages, tools=TOOL_SCHEMAS)

        if resp.get("tool_calls"):
            messages.append({
                "role": "assistant",
                "content": resp.get("content") or "",
                "tool_calls": resp["tool_calls"],
            })

            yield f"🔍 正在分析...\n\n"

            for tc in resp["tool_calls"]:
                fn = tc["function"]
                tool_name = fn["name"]
                try:
                    args = json.loads(fn["arguments"])
                except json.JSONDecodeError:
                    args = {}
                # 前端/上下文传入的 field_id 始终覆盖 LLM 的值
                if field_id:
                    args["field_id"] = field_id
                tool_result = await execute_tool(tool_name, args, db)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(tool_result, ensure_ascii=False, default=str),
                })

            # 流式输出最终回复
            async for chunk in provider.stream_chat(messages):
                yield chunk
        else:
            async for chunk in provider.stream_chat(messages):
                yield chunk

    async def _log(self, user_message, field_id, db, current_user, reply, resp=None):
        try:
            from app.models.ai_agent_log import AIAgentLog
            log = AIAgentLog(
                user_id=current_user.get("sub") if current_user else None,
                field_id=field_id,
                agent_type="chat",
                prompt=user_message,
                tool_calls=json.dumps(resp.get("tool_calls")) if resp and resp.get("tool_calls") else None,
                response=reply[:2000] if reply else None,
                model=resp.get("model") if resp else None,
                tokens_in=resp.get("tokens_in") if resp else None,
                tokens_out=resp.get("tokens_out") if resp else None,
            )
            db.add(log)
            await db.flush()
        except Exception:
            pass

    async def _rule_based(self, user_message: str, field_id: str | None, db) -> str:
        """规则引擎降级方案 — 无需 LLM"""
        msg = user_message.lower()

        if "土壤" in msg or "soil" in msg:
            if not field_id:
                return "请指定田块，我可以帮您分析土壤数据。例如：分析双城试验田A的土壤。"
            result = await execute_tool("analyze_soil", {"field_id": field_id}, db)
        elif "天气" in msg or "weather" in msg:
            if not field_id:
                return "请指定田块，我可以帮您查询天气。例如：查询双城试验田A的天气。"
            result = await execute_tool("get_weather", {"field_id": field_id}, db)
        elif "碳汇" in msg or "carbon" in msg:
            if not field_id:
                return "请指定田块，我可以帮您分析碳汇。例如：分析双城试验田A的碳汇。"
            result = await execute_tool("analyze_carbon", {"field_id": field_id}, db)
        elif "ndvi" in msg or "遥感" in msg:
            if not field_id:
                return "请指定田块，我可以帮您查询 NDVI。例如：查询双城试验田A的NDVI趋势。"
            result = await execute_tool("get_ndvi_trend", {"field_id": field_id, "days": 90}, db)
        else:
            return "我是 AgriSpatial 农业助手。您可以问我：土壤分析、天气预报、碳汇诊断、NDVI 趋势。\n\n💡 提示：配置 DeepSeek API Key 可获得更智能的对话体验。"

        return json.dumps(result, ensure_ascii=False, default=str) if isinstance(result, dict) else str(result)
