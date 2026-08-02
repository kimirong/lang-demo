"""Phase 4 · 任务2：Multi-agent —— 手搭 supervisor 主管-员工模式

模式：一个"主管"节点 + 若干"员工"节点。
  - 主管绑定了两个"分派工具"（RouteToResearcher / RouteToAnalyst），
    用【工具调用】来决定把任务派给谁 —— 这就是路由的本质。
  - 员工干完活，把结果写回消息流，控制权回到主管。
  - 主管觉得可以收尾了就 END。

这样主管与员工各司其职，还能多轮协作（主管可以先派研究员、再派分析师）。
"""

from typing import Literal

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from pydantic import BaseModel, Field

from model import get_llm

llm = get_llm()


# ---------- 1. 主管的"分派工具"（用 Pydantic 定义成工具 schema）----------
class RouteToResearcher(BaseModel):
    """把任务分派给研究员子代理。"""

    query: str = Field(description="要研究员处理的问题")


class RouteToAnalyst(BaseModel):
    """把任务分派给分析师子代理。"""

    query: str = Field(description="要分析师处理的问题")


supervisor_llm = llm.bind_tools([RouteToResearcher, RouteToAnalyst])


# ---------- 2. 三个节点 ----------
def supervisor(state: MessagesState) -> dict:
    """主管：判断该派给谁。会"调用工具"表示要分派，或直接回答表示收尾。"""
    sys = SystemMessage(
        content="你是主管。根据用户问题决定派给谁："
        "需要查证事实/背景资料 → 调用 RouteToResearcher；"
        "需要解读数据/做判断 → 调用 RouteToAnalyst；"
        "自己能答就直接回答。"
    )
    return {"messages": [supervisor_llm.invoke([sys] + state["messages"])]}


def clean_messages(messages) -> list:
    """去掉挂着未完成 tool_calls 的 AI 消息（主管的"分派"消息，不该传给员工）。

    否则消息序列里出现"只有 tool_calls 没有 ToolMessage"，API 会拒绝。
    """
    return [m for m in messages if not (isinstance(m, AIMessage) and m.tool_calls)]


def _worker_reply(state: MessagesState, sys_prompt: str) -> dict:
    """员工通用逻辑：回答主管分派的问题，并把回答【回填成 ToolMessage】。

    关键：主管的"分派"是一次工具调用，员工的工作结果必须作为这个
    工具调用的返回值(ToolMessage)交给主管 —— 这就是 handoff 的本质。
    """
    answer = llm.invoke([SystemMessage(content=sys_prompt)] + clean_messages(state["messages"]))
    # 主管分派消息里的每个 tool_call，都要补一个对应的 ToolMessage
    tool_messages = [
        ToolMessage(content=answer.content, tool_call_id=tc["id"])
        for tc in state["messages"][-1].tool_calls
    ]
    return {"messages": tool_messages}


def researcher(state: MessagesState) -> dict:
    """员工 A：研究员。"""
    return _worker_reply(state, "你是研究员，负责查证事实、提供背景资料。回答精炼。")


def analyst(state: MessagesState) -> dict:
    """员工 B：分析师。"""
    return _worker_reply(state, "你是数据分析师，负责解读数据、给出判断。回答精炼。")


# ---------- 3. 条件边：主管调了哪个工具就去哪个员工 ----------
def route_supervisor(state: MessagesState) -> Literal["researcher", "analyst", END]:
    last: AIMessage = state["messages"][-1]
    if last.tool_calls:
        name = last.tool_calls[0]["name"]
        if name == "RouteToResearcher":
            print(f"  🧭 主管分派给：研究员")
            return "researcher"
        if name == "RouteToAnalyst":
            print(f"  🧭 主管分派给：分析师")
            return "analyst"
    print("  🧭 主管直接回答（收尾）")
    return END


# ---------- 4. 组装 ----------
builder = StateGraph(MessagesState)
builder.add_node("supervisor", supervisor)
builder.add_node("researcher", researcher)
builder.add_node("analyst", analyst)
builder.add_edge(START, "supervisor")
builder.add_conditional_edges(
    "supervisor", route_supervisor, {"researcher": "researcher", "analyst": "analyst", END: END}
)
builder.add_edge("researcher", "supervisor")  # 员工干完回到主管
builder.add_edge("analyst", "supervisor")

graph = builder.compile()


def run(question: str):
    print("=" * 60)
    print(f"用户问题：{question}")
    print("-" * 60)
    result = graph.invoke({"messages": [{"role": "user", "content": question}]})
    print("-" * 60)
    print("最终回答：", result["messages"][-1].content)
    print()


run("帮我查一下 2024 年诺贝尔文学奖得主是谁？")
run("月度销售额：1月 100万，2月 130万，3月 90万。帮我分析一下这个趋势。")
run("你好！")
