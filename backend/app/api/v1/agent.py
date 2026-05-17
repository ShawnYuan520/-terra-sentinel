"""AI 对话助手 API — HTTP + WebSocket 流式"""
import json
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from app.core.database import get_db, AsyncSessionLocal
from app.core.deps import get_current_user
from app.core.security import decode_access_token
from app.agents.llm_router import AgentRouter

router = APIRouter(prefix="/agent", tags=["AI 助手"])


class AgentChatRequest(BaseModel):
    message: str = Field(..., description="用户问题")
    field_id: str | None = Field(None, description="关联田块 ID")


class AgentChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    data: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    agent = AgentRouter()
    reply = await agent.chat(data.message, data.field_id, db, current_user)
    return AgentChatResponse(reply=reply or "抱歉，暂时无法处理您的请求")


@router.websocket("/ws")
async def agent_ws_chat(websocket: WebSocket):
    """WebSocket 流式 AI 对话 — 需通过 ?token=JWT 认证"""
    await websocket.accept()

    # 等待第一条消息（应包含认证 token）
    try:
        raw = await websocket.receive_text()
    except WebSocketDisconnect:
        return

    try:
        init_data = json.loads(raw)
        token = init_data.get("token", "")
        payload = decode_access_token(token)
        if not payload:
            await websocket.send_text(json.dumps({"type": "error", "text": "认证失败，请重新登录"}))
            await websocket.close()
            return
        current_user = payload
        message = init_data.get("message", "")
        field_id = init_data.get("field_id")
    except Exception:
        await websocket.send_text(json.dumps({"type": "error", "text": "无效请求"}))
        await websocket.close()
        return

    await websocket.send_text(json.dumps({"type": "ready", "text": "连接成功"}))

    agent = AgentRouter()

    async with AsyncSessionLocal() as db:
        try:
            if message:
                async for chunk in agent.stream_chat(message, field_id, db, current_user):
                    await websocket.send_text(json.dumps({"type": "chunk", "text": chunk}))
                await websocket.send_text(json.dumps({"type": "done"}))

            while True:
                raw = await websocket.receive_text()
                data = json.loads(raw)
                message = data.get("message", "")
                field_id = data.get("field_id")

                if message.lower() in ("exit", "quit", "退出"):
                    await websocket.send_text(json.dumps({"type": "done"}))
                    break

                async for chunk in agent.stream_chat(message, field_id, db, current_user):
                    await websocket.send_text(json.dumps({"type": "chunk", "text": chunk}))

                await websocket.send_text(json.dumps({"type": "done"}))

        except WebSocketDisconnect:
            pass
        except Exception as e:
            await websocket.send_text(json.dumps({"type": "error", "text": str(e)}))
