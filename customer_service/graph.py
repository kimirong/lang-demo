"""构建并编译客服 agent 图。

结构复用 Phase 3 手搓的 agent 循环（08_handrolled_agent.py）：
  START → agent →(有 tool_calls)→ tools → agent → … →(无 tool_calls)→ END

增强点：
  - 三个工具：lookup_manual(RAG) / calculate / submit_order(带 interrupt 审批)
  - SqliteSaver checkpointer：多轮记忆持久化到 data/checkpoints.db（跨重启不丢）
  - 编译结果以单例提供，FastAPI 复用同一张图
"""

import sqlite3
from typing import Literal

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, MessagesState, StateGraph

from model import get_llm

from .tools import TOOLS

SYSTEM_PROMPT = """你是「星辰科技」的智能客服助手。

你有以下能力：
1. 查《员工手册》回答公司制度问题（试用期、考勤、年假、福利、晋升、离职、请假等）→ 调用 lookup_manual
2. 做数学计算 → 调用 calculate
3. 帮用户下单 → 调用 submit_order（下单会自动申请人工审批，请向用户说明正在等待确认）

回答要求：简洁、友好、直接；依据《员工手册》检索到的资料回答，不要编造公司制度。
"""

# temperature=0：工具调用 agent 必须确定性（模型"该调工具就调工具"，不要随机闲聊）
_llm = get_llm(temperature=0).bind_tools(TOOLS)
_TOOLS_BY_NAME = {t.name: t for t in TOOLS}


# ---------- 节点 ----------
def agent_node(state: MessagesState) -> dict:
    """思考：把完整对话交给 DeepSeek，它决定回答还是调用工具。"""
    return {"messages": [_llm.invoke([SystemMessage(content=SYSTEM_PROMPT)] + state["messages"])]}


def tools_node(state: MessagesState) -> dict:
    """行动：执行上一条 AI 消息里的所有工具调用，结果作为 ToolMessage 追加。"""
    last: AIMessage = state["messages"][-1]
    results = []
    for tc in last.tool_calls:
        print(f"  ⚙️ 调用工具: {tc['name']}({tc['args']})")
        observation = _TOOLS_BY_NAME[tc["name"]].invoke(tc["args"])
        results.append(ToolMessage(content=observation, tool_call_id=tc["id"]))
    return {"messages": results}


# ---------- 条件边 ----------
def should_continue(state: MessagesState) -> Literal["tools", END]:
    return "tools" if state["messages"][-1].tool_calls else END


def _build():
    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", tools_node)
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    builder.add_edge("tools", "agent")

    # 手动建连接并保持打开（应用整个生命周期复用）；
    # check_same_thread=False 允许 FastAPI 线程池跨线程读写。
    conn = sqlite3.connect("data/checkpoints.db", check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    return builder.compile(checkpointer=checkpointer)


_graph = None


def get_graph():
    """返回编译好的客服 agent（单例）。"""
    global _graph
    if _graph is None:
        _graph = _build()
    return _graph
