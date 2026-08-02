"""Phase 4 · 任务1：Human-in-the-loop —— interrupt 暂停等人审批

场景：agent 准备"下单"，但下单前必须经过人确认，这是很多生产应用的硬需求。

机制：
  - interrupt(payload)：让图在这一步暂停，并把 payload 抛给外部。
    调用方拿到后展示给用户；用户答复后，用 Command(resume=答复) 恢复执行。
  - interrupt() 的返回值 = 恢复时传入的 resume 内容（关键理解！）
  - 必须配 checkpointer：暂停/恢复依赖持久化的线程状态。

流程演示（终端里模拟两个人分别批准/拒绝）：
  approve_node 暂停 → 显示订单 → 传 approve=True/False → 图继续 → 输出结果
"""

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from typing_extensions import TypedDict


class OrderState(TypedDict):
    result: str  # 最终结果


def submit_order_node(state: OrderState) -> dict:
    """下单节点：先暂停，把订单详情抛给人类审批。

    interrupt() 在这里"堵住"，直到有人用 Command(resume=...) 恢复，
    返回值就是 resume 里带过来的内容。
    """
    decision = interrupt(
        {
            "action": "submit_order",
            "order": "iPhone 15 · 黑色 · ¥5999",
            "question": "是否批准这笔下单？",
        }
    )
    if decision.get("approved"):
        return {"result": f"✅ 下单成功，订单：{decision.get('order', '')}，收货地址：{decision.get('address', '未填')}"}
    return {"result": f"❌ 下单被拒绝，原因：{decision.get('reason', '未说明')}"}


builder = StateGraph(OrderState)
builder.add_node("submit_order", submit_order_node)
builder.add_edge(START, "submit_order")
builder.add_edge("submit_order", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "order-001"}}

print("=" * 60)
print("第一次 invoke：图会跑进 submit_order 然后【暂停】")
print("=" * 60)
result = graph.invoke({}, config=config)
print("invoke 返回（此时图没跑完，只是把能算的算出来了）：", result)
print("当前停在哪里（next 节点）：", graph.get_state(config).next)

# 暂停时抛给外部的内容（真实应用里这就是要给用户看的审批卡片）
# 注意：interrupt 的 payload 在 invoke 的返回值里（__interrupt__ 键）
interrupt_payload = result["__interrupt__"]
for item in interrupt_payload:
    print("\n--- 需要人工审批的内容 ---")
    print(f"  动作: {item.value['action']}")
    print(f"  订单: {item.value['order']}")
    print(f"  问题: {item.value['question']}")

print()
print("=" * 60)
print("场景 1：用户点击【批准】")
print("=" * 60)
resumed = graph.invoke(Command(resume={"approved": True, "order": "iPhone 15 黑色 ¥5999", "address": "北京市朝阳区xxx"}), config=config)
print("最终结果：", resumed["result"])

print()
print("=" * 60)
print("场景 2：另一个订单，用户点击【拒绝】")
print("=" * 60)
config2 = {"configurable": {"thread_id": "order-002"}}
graph.invoke({}, config=config2)  # 同样暂停在审批
resumed2 = graph.invoke(Command(resume={"approved": False, "reason": "预算不够"}), config=config2)
print("最终结果：", resumed2["result"])

print()
print(">>> 关键理解：interrupt() 暂停的不是进程，而是这个线程的图执行。")
print(">>> 暂停后可以任意等待，甚至可以换台机器恢复——只要 thread_id 一致。")
