"""Phase 3 · 任务1：StateGraph 三大件——State / 节点 / 边

LangGraph 把工作流建模成"图"，核心概念：
  1. State —— 整个图共享的"画板"，所有节点都能读、能改
  2. 节点(node) —— 一个函数，接收 State，返回要更新到 State 的字段
  3. 边(edge) —— 决定执行流向；条件边可以按 State 内容动态选下一个节点

本脚本故意不用 LLM，先纯逻辑把"图是怎么跑的"讲清楚。
最后用 graph.get_graph() 把图画出来看。
"""

import operator
from typing import Annotated, Literal

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict


# ========== 1. 定义 State ==========
class State(TypedDict):
    query: str
    category: str  # 分类结果
    # Annotated[list, operator.add] 是"规约器(reducer)"：
    # 多个节点往 path 里加内容时，会自动合并(拼接)，而不是覆盖
    path: Annotated[list[str], operator.add]  # 记录执行路径，方便观察


# ========== 2. 定义节点（都是普通函数）==========
def classify(state: State) -> dict:
    """规则式分类：根据问题关键词判断类别。"""
    q = state["query"]
    if any(k in q for k in ["python", "代码", "编程", "接口"]):
        cat = "tech"
    elif any(k in q for k in ["唐朝", "明朝", "历史", "皇帝"]):
        cat = "history"
    else:
        cat = "other"
    return {"category": cat, "path": ["classify"]}  # 返回的字段会写回 State


def tech_answer(state: State) -> dict:
    return {"path": ["tech"]}


def history_answer(state: State) -> dict:
    return {"path": ["history"]}


def fallback(state: State) -> dict:
    return {"path": ["fallback"]}


# ========== 3. 条件边：根据 State 动态路由 ==========
def route(state: State) -> Literal["tech", "history", "fallback"]:
    """返回值决定下一步去哪个节点。"""
    return state["category"]


# ========== 4. 组装图 ==========
builder = StateGraph(State)
builder.add_node("classify", classify)
builder.add_node("tech", tech_answer)
builder.add_node("history", history_answer)
builder.add_node("fallback", fallback)

builder.add_edge(START, "classify")
# 条件边：classify 之后，按 route() 的结果跳转。
# 注意：映射表必须覆盖 route() 可能返回的所有值，漏一个就 KeyError。
builder.add_conditional_edges(
    "classify",
    route,
    {"tech": "tech", "history": "history", "other": "fallback"},
)
builder.add_edge("tech", END)
builder.add_edge("history", END)
builder.add_edge("fallback", END)

graph = builder.compile()  # 编译后才能真正调用

# ========== 5. 运行 ==========
for q in ["帮我写一段 Python 代码", "唐朝是什么时候建立的", "今天天气怎么样"]:
    result = graph.invoke({"query": q})
    print(f"问题：{q}")
    print(f"  分类: {result['category']:<8} 执行路径: {' → '.join(result['path'])}")

print("\n" + "=" * 60)
print("图的内部结构（Mermaid 可视化文本）")
print("=" * 60)
print(graph.get_graph().draw_mermaid())
