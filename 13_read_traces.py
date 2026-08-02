"""Phase 5 · 任务2：用 SDK 读 trace —— 理解 agent 的"体检报告"

LangChain 自动埋点后，每次调用都是一棵树（根 = 整体运行，叶子 = 各 llm/工具调用）。
本脚本：
  1. 跑一个带工具的 agent（触发一次完整的"思考→行动→观察"）
  2. 从 LangSmith 拉出最新这棵 trace 树
  3. 打印每个节点：类型 / 耗时 / 输入 / 输出 / token 消耗
  4. 演示"定位问题"：哪一步最耗时、token 花在哪

这就像给 agent 做体检——生产环境里排查"为什么慢/为什么贵"就靠它。
"""

import time
from typing import Literal

from langchain.tools import tool
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, MessagesState, StateGraph

# model 必须首个 import（设置 HF_HUB_OFFLINE + 加载 .env 里的 LANGSMITH 配置）
from model import get_llm

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


# ========== 1. 构造一个带工具的 agent（和 08 手搓版结构一致） ==========
@tool
def calculate(expression: str) -> str:
    """计算一个数学表达式并返回数值结果。"""
    try:
        return f"计算结果: {eval(expression)}"
    except Exception as e:
        return f"表达式无法计算: {e}"


TOOLS = {"calculate": calculate}
llm = get_llm().bind_tools([calculate])


def agent(state: MessagesState) -> dict:
    return {"messages": [llm.invoke([SystemMessage(content="你是助手。")] + state["messages"])]}


def tools_node(state: MessagesState) -> dict:
    last = state["messages"][-1]
    results = []
    for tc in last.tool_calls:
        results.append(ToolMessage(content=TOOLS[tc["name"]].invoke(tc["args"]), tool_call_id=tc["id"]))
    return {"messages": results}


def should_continue(state: MessagesState) -> Literal["tools", END]:
    return "tools" if state["messages"][-1].tool_calls else END


builder = StateGraph(MessagesState)
builder.add_node("agent", agent)
builder.add_node("tools", tools_node)
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
builder.add_edge("tools", "agent")
graph = builder.compile()

# 跑一次，制造一棵 trace 树
print("运行 agent（同时生成 trace）...")
graph.invoke({"messages": [{"role": "user", "content": "帮我算 (12+8)*3 等于多少？"}]})

# ========== 2. 从 LangSmith 拉取最新的 trace 树 ==========
from langsmith import Client  # noqa: E402

client = Client()
# execution_order=1 只拿"根"运行（整体），按开始时间取最新的
root_runs = list(client.list_runs(project_name="lang-demo", execution_order=1, limit=3))
if not root_runs:
    print("没找到 trace")
    raise SystemExit(1)

# 等云端索引一下，避免读到旧数据
time.sleep(1)
root = root_runs[0]
print(f"\n最新根运行：{root.name}  (类型 {root.run_type})")


# ========== 3. 递归打印整棵树 ==========
def print_run(run, indent=""):
    latency = (run.end_time - run.start_time).total_seconds() if run.end_time and run.start_time else 0
    usage = ""
    if run.extra and run.extra.get("usage") and run.extra["usage"].get("token_usage"):
        t = run.extra["usage"]["token_usage"]
        usage = f"  token: in={t.get('input_tokens', '?')} out={t.get('output_tokens', '?')}"
    out_preview = str(run.outputs)[:70] if run.outputs else ""
    print(f"{indent}[{run.run_type}] {run.name}  ({latency:.2f}s){usage}")
    if out_preview:
        print(f"{indent}    输出: {out_preview}")

    children = list(client.list_runs(parent_run_id=run.id, limit=20))
    for child in children:
        print_run(child, indent + "  ")


print("\n" + "=" * 60)
print("trace 树（根 → 叶子）")
print("=" * 60)
print_run(root)

# ========== 4. 定位问题：哪个节点最耗时 / 最费 token ==========
print("\n" + "=" * 60)
print("问题定位：找出最耗时的步骤")
print("=" * 60)


def walk(run, collect):
    collect.append(run)
    for child in client.list_runs(parent_run_id=run.id, limit=20):
        walk(child, collect)


all_runs = []
walk(root, all_runs)
# 排除根节点本身（它必然最长），找真正消耗时间的"叶子"步骤
non_root = [r for r in all_runs if r.id != root.id]
slowest = max(
    non_root,
    key=lambda r: (r.end_time - r.start_time).total_seconds() if r.end_time and r.start_time else 0,
)
if slowest.end_time and slowest.start_time:
    print(f"  最耗时的子步骤: {slowest.name} [{slowest.run_type}] "
          f"({(slowest.end_time - slowest.start_time).total_seconds():.2f}s)")
print(">>> 生产排查思路：先看根耗时 → 找最慢的子节点 → 看它的输入/输出是否合理。")
