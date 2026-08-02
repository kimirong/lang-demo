"""Phase 6 · 端到端测试：覆盖客服 API 的全部流程。

用 FastAPI 的 TestClient（不需要真的起服务器），顺序验证：
  1. 健康检查
  2. RAG 问答（查员工手册）
  3. 计算工具
  4. 多轮记忆（SqliteSaver 跨请求持久）
  5. 下单触发人工审批（pending_approval）
  6. 批准下单 → 成功
  7. 拒绝下单 → 失败
  8. 会话历史

运行：.venv/bin/python test_api.py
"""

import os

# 重要：会话状态持久化在 data/checkpoints.db，会【跨运行残留】。
# 测试必须重置，否则上一轮的会话历史会干扰本轮的断言。
for f in ["data/checkpoints.db", "data/checkpoints.db-wal", "data/checkpoints.db-shm"]:
    if os.path.exists(f):
        os.remove(f)

from fastapi.testclient import TestClient  # noqa: E402

from app import app  # noqa: E402  （reset 之后才 import，保证拿到全新的 checkpointer）

client = TestClient(app)

passed: list[bool] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    passed.append(cond)
    mark = "✓" if cond else "✗"
    print(f"  {mark} {name}  {detail}")


print("=" * 60)
print("1) 健康检查")
print("=" * 60)
r = client.get("/health")
check("health", r.status_code == 200 and r.json()["status"] == "ok")

print()
print("=" * 60)
print("2) RAG 问答（查员工手册）")
print("=" * 60)
r = client.post("/chat", json={"session_id": "t-rag", "message": "新员工的试用期是多久？"})
body = r.json()
check("状态", body["status"] == "ok", body.get("reply", "")[:30])
check("答案含试用期+3", "试用期" in body["reply"] and "3" in body["reply"], body.get("reply", "")[:40])

print()
print("=" * 60)
print("3) 计算工具")
print("=" * 60)
r = client.post("/chat", json={"session_id": "t-calc", "message": "帮我算一下 (12+8)*3 等于多少？"})
body = r.json()
check("计算结果含60", body["status"] == "ok" and "60" in body["reply"], body.get("reply", "")[:40])

print()
print("=" * 60)
print("4) 多轮记忆（同一 session 跨请求记住上下文）")
print("=" * 60)
client.post("/chat", json={"session_id": "t-mem", "message": "我叫小明，请记住"})
r = client.post("/chat", json={"session_id": "t-mem", "message": "我叫什么名字？"})
body = r.json()
check("记住名字", "小明" in body.get("reply", ""), body.get("reply", "")[:40])

print()
print("=" * 60)
print("5) 下单触发人工审批")
print("=" * 60)
r = client.post(
    "/chat",
    json={"session_id": "t-order", "message": "我要下单买一部 iPhone 15 黑色，价格 5999 元，收货地址北京市朝阳区一号楼"},
)
body = r.json()
check("返回 pending_approval", body["status"] == "pending_approval")
if body["status"] == "pending_approval":
    it = body["interrupt"]
    check("审批内容", it["action"] == "submit_order" and "iPhone" in it["product"], str(it)[:50])

print()
print("=" * 60)
print("6) 批准下单")
print("=" * 60)
r = client.post("/approve", json={"session_id": "t-order", "approved": True, "note": "北京市朝阳区一号楼"})
body = r.json()
check("下单成功", body["status"] == "ok" and "成功" in body["reply"], body.get("reply", "")[:50])

print()
print("=" * 60)
print("7) 拒绝下单（新会话）")
print("=" * 60)
r = client.post(
    "/chat",
    json={"session_id": "t-reject", "message": "我要下单买一台笔记本电脑，价格 8000 元，收货地址上海市浦东新区二号楼"},
)
body = r.json()
check("拒绝场景先触发审批", body["status"] == "pending_approval", str(body.get("interrupt", ""))[:40])
r = client.post("/approve", json={"session_id": "t-reject", "approved": False, "note": "预算不够"})
body = r.json()
check("拒绝下单", "拒绝" in body.get("reply", ""), body.get("reply", "")[:50])

print()
print("=" * 60)
print("8) 会话历史")
print("=" * 60)
r = client.get("/history/t-rag")
body = r.json()
check("历史非空", r.status_code == 200 and body["message_count"] >= 2, f"共 {body['message_count']} 条")

print()
print("=" * 60)
print(f"结果：{sum(passed)}/{len(passed)} 通过")
print("=" * 60)
assert all(passed), "存在失败用例，请检查"
print("✅ 全部通过！")
