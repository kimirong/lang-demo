"""Phase 3 · 任务2：手搓 agent 的"思考→行动→观察"循环

Phase 1 里 create_agent 一行代码就自动跑了 agent。这一课我们把它的
内部机制拆开，用 StateGraph 亲手搭一遍。理解了这里，agent 就再也不是黑盒。

循环结构（就是一个图上的环）：
    START → agent(思考:LLM 决定要不要调工具)
                │
                ├─ 有 tool_calls ──→ tools(行动:执行工具) ──┐
                │                                            │ (观察结果回到agent)
                └─ 没有 ──→ END（直接回答）
"""

from typing import Literal

from langchain.tools import tool
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, MessagesState, StateGraph

from model import get_llm


# ---------- 工具 ----------
@tool
def calculate(expression: str) -> str:
    """计算一个数学表达式并返回数值结果。

    Args:
        expression: 数学表达式，例如 "2 + 3 * 4" 或 "(12+8)/4"
    """
    try:
        return f"计算结果: {eval(expression)}"  # 教学演示，生产勿用 eval
    except Exception as e:
        return f"表达式无法计算: {e}"


TOOLS = {"calculate": calculate}
llm = get_llm()
llm_with_tools = llm.bind_tools([calculate])

SYSTEM_PROMPT = "你是一个乐于助人的助手。需要计算时调用 calculate 工具。"


# ---------- 节点 1：agent（思考）----------
def agent(state: MessagesState) -> dict:
    """把当前消息喂给 LLM，模型自己决定：回答，还是请求调用工具。"""
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response: AIMessage = llm_with_tools.invoke(messages)
    return {"messages": [response]}  # 追加一条 AI 消息到 State


# ---------- 节点 2：tools（行动）----------
def tools_node(state: MessagesState) -> dict:
    """执行上一条 AI 消息里的所有工具调用，把结果作为 ToolMessage 追加。"""
    last_message = state["messages"][-1]
    results = []
    for tool_call in last_message.tool_calls:
        print(f"  ⚙️  调用工具 {tool_call['name']}({tool_call['args']})")
        observation = TOOLS[tool_call["name"]].invoke(tool_call["args"])
        results.append(
            ToolMessage(content=observation, tool_call_id=tool_call["id"])
        )
    return {"messages": results}


# ---------- 条件边：决定继续循环还是结束 ----------
def should_continue(state: MessagesState) -> Literal["tools", END]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:  # 模型要调用工具 → 去执行
        return "tools"
    return END  # 模型直接回答 → 结束


# ---------- 组装图 ----------
builder = StateGraph(MessagesState)
builder.add_node("agent", agent)
builder.add_node("tools", tools_node)
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
builder.add_edge("tools", "agent")  # 关键：执行完工具回到 agent 再"思考"

agent_graph = builder.compile()

# ---------- 运行 ----------
print("=" * 60)
print("场景 1：需要多轮工具调用")
print("=" * 60)
result = agent_graph.invoke({"messages": [{"role": "user", "content": "帮我算 (12+8)*3，然后再算 (12+8)*3*2"}]})
for m in result["messages"]:
    m.pretty_print()

print()
print("=" * 60)
print("场景 2：不需要工具")
print("=" * 60)
result = agent_graph.invoke({"messages": [{"role": "user", "content": "你好，你是谁？"}]})
for m in result["messages"]:
    m.pretty_print()

print()
print("=" * 60)
print("对比：Phase 1 里 create_agent 一行代码 = 上面整张图")
print("=" * 60)
from langchain.agents import create_agent  # noqa: E402
agent_auto = create_agent(model=get_llm(), tools=[calculate])
r = agent_auto.invoke({"messages": [{"role": "user", "content": "帮我算 (12+8)*3"}]})
r["messages"][-1].pretty_print()
