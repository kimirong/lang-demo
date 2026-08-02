"""Phase 0 · 第一条 DeepSeek 对话

演示 LangChain 1.x 里接入 DeepSeek（OpenAI 兼容接口）的最小用法：
  1. 普通调用 invoke
  2. 流式输出 stream
  3. 多轮对话（消息列表）
"""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# 读取 .env 中的密钥
load_dotenv()

# DeepSeek 提供 OpenAI 兼容的 HTTP 接口，所以直接用 ChatOpenAI，
# 只需覆盖 base_url 和 model 即可。
llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    temperature=0.7,
)

print("=" * 60)
print("1) invoke —— 一次性拿到完整回复")
print("=" * 60)
reply = llm.invoke("用一句话介绍什么是 LangChain。")
print(reply.content)
print()

print("=" * 60)
print("2) stream —— 流式吐出 token")
print("=" * 60)
for chunk in llm.stream("用一句话介绍什么是 LangGraph。"):
    print(chunk.content, end="", flush=True)
print("\n")

print("=" * 60)
print("3) 多轮对话 —— 传入消息列表，让模型记住上文")
print("=" * 60)
messages = [
    SystemMessage(content="你是一个耐心的 Python 老师，回答要简洁。"),
    HumanMessage(content="LangChain 和 LangGraph 有什么区别？"),
]
reply = llm.invoke(messages)
print("助手：", reply.content)
