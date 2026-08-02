"""Phase 4 · 任务3：长期记忆 —— InMemoryStore（语义检索）

对比：
  09 的 checkpointer(thread_id) = 短期记忆：只在"同一会话"里有效，换线程就丢。
  本课的 InMemoryStore             = 长期记忆：按用户维度存储，跨会话/跨线程，
                                    且支持【语义检索】（用向量找相关记忆）。

关键 API：
  store.put(namespace, key, value)        存一条记忆
  store.search(namespace, query=...)      语义搜索最相关的记忆
  编译图时传 store=store，节点里注入到提示词
"""

# 必须最先 import：model.py 设置 HF_HUB_OFFLINE（见 05/06 的教训）
from model import get_llm

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.store.memory import InMemoryStore
from langchain_huggingface import HuggingFaceEmbeddings

# ========== 1. 建 store，带语义索引（用本地 bge embedding） ==========
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
store = InMemoryStore(
    index={
        "embed": embeddings.embed_documents,  # 传入向量化函数
        "dims": 512,                          # bge-small-zh 的向量维度
        "fields": ["content"],                # 对存储值里的 content 字段做索引
    }
)

# ========== 2. 预先存几条"用户画像"记忆 ==========
NAMESPACE = ("user-1", "memories")
store.put(NAMESPACE, "style", {"content": "用户喜欢简洁直接的回答，讨厌冗长啰嗦。"})
store.put(NAMESPACE, "role", {"content": "用户是电商产品经理，正在做个性化推荐项目。"})
store.put(NAMESPACE, "pref", {"content": "用户偏好中文回复，术语要附上中文解释。"})
print("已存入 3 条长期记忆（用户：user-1）\n")

# ========== 3. 演示语义检索（不用精确关键词也能命中） ==========
print("=" * 60)
print("语义检索演示：搜「别废话，直接说重点」")
print("=" * 60)
hits = store.search(NAMESPACE, query="别废话，直接说重点", limit=2)
for h in hits:
    print(f"  命中: {h.value['content']}   (score={h.score:.3f})")

# ========== 4. 图：节点里检索记忆 → 注入提示词 ==========
llm = get_llm()


def agent_with_memory(state: MessagesState) -> dict:
    # 1) 用最新用户消息做语义检索，找出相关的长期记忆
    query = state["messages"][-1].content
    memories = store.search(NAMESPACE, query=query, limit=3)
    memory_text = "\n".join(f"- {m.value['content']}" for m in memories)

    # 2) 把记忆拼进系统提示词，让模型"想起"这个用户
    sys = SystemMessage(
        content="你是有长期记忆的助手。关于这位用户的记忆：\n"
        + (memory_text or "（暂无相关记忆）")
        + "\n\n请结合记忆调整回答方式。"
    )
    return {"messages": [llm.invoke([sys] + state["messages"])]}


builder = StateGraph(MessagesState)
builder.add_node("agent", agent_with_memory)
builder.add_edge(START, "agent")
builder.add_edge("agent", END)
graph = builder.compile()

# ========== 5. 跨线程验证：换 thread_id，记忆依然生效 ==========
print()
print("=" * 60)
print("跨线程验证（每次都是新会话 thread_id，但长期记忆仍在）")
print("=" * 60)
for i, q in enumerate(
    ["你好，你是谁？", "顺便问下，我是什么职业？", "我平时喜欢什么样的回答风格？"]
):
    # 注意：每次都换新的 thread_id —— 短期记忆必然失效，能答对全靠长期记忆
    result = graph.invoke(
        {"messages": [{"role": "user", "content": q}]},
        config={"configurable": {"thread_id": f"fresh-session-{i}"}},
    )
    print(f"\n[会话{i}] 问：{q}")
    print(f"  答：{result['messages'][-1].content[:90]}")

print()
print(">>> 一句话总结：thread_id 管『这一场对话』，store 管『这个人一直记得什么』。")
