"""Phase 1 · 提示词模板 + LCEL 管道

核心概念：
  1. ChatPromptTemplate —— 消息模板，支持 {变量} 占位符
  2. LCEL（|）—— 把"模板→模型→解析器"串成一条可复用的链
  3. StrOutputParser —— 从模型回复中取出纯文本
"""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from model import get_llm

llm = get_llm()

# --- 1. 消息模板：用 {role} / {question} 占位 ---
# from_messages 依次定义系统消息和人类消息
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一位{role}，回答要简洁、准确，不要客套。"),
        ("human", "{question}"),
    ]
)

# --- 2. LCEL 管道：prompt | llm | parser ---
# 前一步的输出自动作为下一步的输入
chain = prompt | llm | StrOutputParser()

print("=" * 60)
print("LCEL 链：prompt | llm | StrOutputParser")
print("=" * 60)

# invoke 时传入模板里的变量
result = chain.invoke({"role": "历史老师", "question": "秦始皇统一六国是哪一年？"})
print("历史老师版：", result)

result = chain.invoke({"role": "程序员", "question": "什么是列表推导式？"})
print("程序员版：", result)

# --- 3. stream：管道同样支持流式 ---
print()
print("=" * 60)
print("stream 流式（管道也支持）")
print("=" * 60)
for chunk in chain.stream({"role": "诗人", "question": "用一句诗形容秋天。"}):
    print(chunk, end="", flush=True)
print()
