"""Phase 1 · 产出2：单工具 agent 雏形

核心概念：
  1. @tool —— 把一个 Python 函数变成"模型可调用的工具"。
     docstring 自动成为工具的说明，参数类型自动成为入参 schema。
  2. create_agent —— 一行代码把模型+工具编排成 agent。
     模型会自己决定：这道题要调用工具吗？调用哪个？参数填什么？
  3. 观察 agent 的完整思考轨迹（messages 里的 AIMessage.tool_calls）

注意：这是教学 demo，生产环境不要用 eval()，会有注入风险。
"""

from langchain.agents import create_agent
from langchain.tools import tool

from model import get_llm


# --- 1. 用 @tool 定义一个计算器工具 ---
@tool
def calculate(expression: str) -> str:
    """计算一个数学表达式并返回数值结果。

    Args:
        expression: 数学表达式，例如 "2 + 3 * 4" 或 "(12+8)/4"
    """
    try:
        return f"计算结果: {eval(expression)}"  # 教学演示，生产请勿直接用 eval
    except Exception as e:
        return f"表达式无法计算: {e}"


# --- 2. 创建 agent：模型 + 工具 ---
agent = create_agent(model=get_llm(), tools=[calculate])

print("=" * 60)
print("场景 1：需要调用工具的问题")
print("=" * 60)
result = agent.invoke(
    {"messages": [{"role": "user", "content": "帮我算一下 (12+8) * 3 等于多少？"}]}
)
for msg in result["messages"]:
    msg.pretty_print()

print()
print("=" * 60)
print("场景 2：不需要工具的问题（agent 应直接回答）")
print("=" * 60)
result = agent.invoke(
    {"messages": [{"role": "user", "content": "你好，你是谁？"}]}
)
for msg in result["messages"]:
    msg.pretty_print()
