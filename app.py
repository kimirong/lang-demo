"""Phase 6 · DeepSeek 智能客服助手 —— FastAPI 入口。

启动：uvicorn app:app --port 8000
端点：
  GET  /health                 存活检查
  POST /chat                   发消息（可能返回 pending_approval 等待审批）
  POST /approve                审批下单（恢复被 interrupt 暂停的图）
  GET  /history/{session_id}   查看会话历史

说明：端点用同步 def（FastAPI 丢线程池执行），避开 async + SqliteSaver 的复杂度。
"""

import uuid

from fastapi import FastAPI
from langgraph.types import Command
from pydantic import BaseModel

from customer_service.graph import get_graph

app = FastAPI(title="DeepSeek 智能客服助手", version="1.0.0")
graph = get_graph()  # 启动时构建一次（含 RAG 向量库 + checkpointer）


# ---------- 请求/响应模型 ----------
class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


class ApproveRequest(BaseModel):
    session_id: str
    approved: bool
    note: str | None = None  # 批准时可为收货地址；拒绝时可为原因


def _last_ai_reply(result: dict) -> str:
    """从结果消息里取最后一条非空 AI 回复。"""
    for msg in reversed(result["messages"]):
        if getattr(msg, "type", "") == "ai" and msg.content:
            return msg.content
    return "(暂无回复)"


def _config(session_id: str) -> dict:
    return {"configurable": {"thread_id": session_id}}


# ---------- 端点 ----------
@app.get("/health")
def health():
    return {"status": "ok", "service": "deepseek-customer-service"}


@app.post("/chat")
def chat(req: ChatRequest):
    sid = req.session_id or uuid.uuid4().hex
    result = graph.invoke(
        {"messages": [{"role": "user", "content": req.message}]},
        config=_config(sid),
    )

    # 下单触发 interrupt → 图暂停，返回审批信息
    if "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        return {"status": "pending_approval", "session_id": sid, "interrupt": payload}

    return {"status": "ok", "session_id": sid, "reply": _last_ai_reply(result)}


@app.post("/approve")
def approve(req: ApproveRequest):
    # 构造 resume 内容，恢复被 interrupt() 暂停的工具执行
    resume = {"approved": req.approved}
    if req.note:
        resume["address" if req.approved else "reason"] = req.note

    result = graph.invoke(Command(resume=resume), config=_config(req.session_id))
    return {"status": "ok", "session_id": req.session_id, "reply": _last_ai_reply(result)}


@app.get("/history/{session_id}")
def history(session_id: str):
    state = graph.get_state(_config(session_id))
    messages = [
        {"role": m.type, "content": m.content}
        for m in state.values.get("messages", [])
    ]
    return {"session_id": session_id, "message_count": len(messages), "messages": messages}
