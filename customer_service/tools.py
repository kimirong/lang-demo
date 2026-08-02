"""客服 agent 的三个工具。

  - lookup_manual：RAG 查《员工手册》
  - calculate：数学计算
  - submit_order：下单（内部调用 interrupt() 暂停，等人审批）
"""

from langchain.tools import tool
from langgraph.types import interrupt

from . import rag


@tool
def lookup_manual(query: str) -> str:
    """在《员工手册》知识库中检索信息。回答公司制度类问题（试用期、考勤、年假、福利、晋升、离职、请假等）时调用。

    Args:
        query: 要查询的问题或关键词，例如「试用期多长」「年假怎么算」
    """
    return rag.retrieve(query)


@tool
def calculate(expression: str) -> str:
    """计算一个数学表达式并返回数值结果。

    Args:
        expression: 数学表达式，例如 "2 + 3 * 4" 或 "(12+8)/4"
    """
    try:
        # 教学演示；生产应用请换成安全求值器（如 ast 解析），避免注入
        return f"计算结果: {eval(expression)}"
    except Exception as e:
        return f"表达式无法计算: {e}"


@tool
def submit_order(product: str, price: str, address: str) -> str:
    """提交商品订单。注意：调用本工具会暂停流程，等待用户人工批准或拒绝后才真正下单。

    Args:
        product: 商品名称，如「iPhone 15 黑色」
        price: 价格，如「5999」
        address: 收货地址
    """
    decision = interrupt(
        {
            "action": "submit_order",
            "product": product,
            "price": price,
            "address": address,
            "question": "是否批准这笔下单？",
        }
    )
    if decision.get("approved"):
        addr = decision.get("address", address)
        return f"下单成功：{product}，¥{price}，收货地址：{addr}"
    return f"下单被拒绝，原因：{decision.get('reason', '未说明')}"


TOOLS = [lookup_manual, calculate, submit_order]
