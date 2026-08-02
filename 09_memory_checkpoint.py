"""Phase 3 · 任务3：checkpointer 持久化 —— 让 agent 记住多轮对话

问题：默认情况下每次 graph.invoke() 都是"全新会话"，上轮对话内容会丢。
解决：编译时传入 checkpointer（这里用 InMemorySaver，内存版；生产可用
      Postgres/Redis 等），再在 invoke 时传 thread_id。
     —— 同一个 thread_id = 同一个会话，状态自动累积。

三个实验：
  A. 无 checkpointer：两次调用互不相识
  B. 有 checkpointer + 同一 thread_id：记得上轮
  C. 有 checkpointer + 不同 thread_id：会话隔离（不串台）
"""

from typing import Literal

from langchain.tools import tool
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph

from model import get_llm


@tool
def calculate(expression: str) -> str:
    """计算一个数学表达式并返回数值结果。

    Args:
        expression: 数学表达式，例如 "2 + 3 * 4" 或 "(12+8)/4"
    """
    try:
        return f"计算结果: {eval(expression)}"
    except Exception as e:
        return f"表达式无法计算: {e}"


TOOLS = {"calculate": calculate}
llm = get_llm()
llm_with_tools = llm.bind_tools([calculate])
SYSTEM_PROMPT = "你是一个乐于助人的助手。"


def agent(state: MessagesState) -> dict:
    return {"messages": [llm_with_tools.invoke([SystemMessage(content=SYSTEM_PROMPT)] + state["messages"])]}


def tools_node(state: MessagesState) -> dict:
    last = state["messages"][-1]
    results = []
    for tc in last.tool_calls:
        observation = TOOLS[tc["name"]].invoke(tc["args"])
        results.append(ToolMessage(content=observation, tool_call_id=tc["id"]))
    return {"messages": results}


def should_continue(state: MessagesState) -> Literal["tools", END]:
    return "tools" if state["messages"][-1].tool_calls else END


def build_agent(checkpointer=None):
    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent)
    builder.add_node("tools", tools_node)
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    builder.add_edge("tools", "agent")
    return builder.compile(checkpointer=checkpointer)


def ask(graph, user_text, thread_id=None):
    """封装一次问答：可选 thread_id。"""
    config = {"configurable": {"thread_id": thread_id}} if thread_id else None
    result = graph.invoke({"messages": [{"role": "user", "content": user_text}]}, config=config)
    return result["messages"][-1].content


# ========== 实验 A：无 checkpointer ==========
print("=" * 60)
print("实验 A：无 checkpointer —— 两次调用互不相识")
print("=" * 60)
graph_no_mem = build_agent()
print("第1轮 我问：我叫小明")
print("  →", ask(graph_no_mem, "我叫小明"))
print("第2轮 我问：我叫什么名字？")
print("  →", ask(graph_no_mem, "我叫什么名字？"), "  ← 记不住，因为状态没保留")

# ========== 实验 B：有 checkpointer + 同一 thread_id ==========
print()
print("=" * 60)
print("实验 B：checkpointer + 同一 thread_id —— 记得上轮")
print("=" * 60)
checkpointer = InMemorySaver()
graph_mem = build_agent(checkpointer=checkpointer)
print("第1轮 我问：我叫小明")
print("  →", ask(graph_mem, "我叫小明", thread_id="user-1"))
print("第2轮 我问：我叫什么名字？")
print("  →", ask(graph_mem, "我叫什么名字？", thread_id="user-1"), "  ← 记住了！")

# ========== 实验 C：不同 thread_id ==========
print()
print("=" * 60)
print("实验 C：不同 thread_id —— 会话隔离")
print("=" * 60)
print("换 thread_id='user-2' 问：我叫什么名字？")
print("  →", ask(graph_mem, "我叫什么名字？", thread_id="user-2"), "  ← 换会话就不记得小明")

print()
print(">>> 一句话总结：thread_id 就是【会话 id】。同一个 id 继续累积历史，不同 id 各聊各的。")
