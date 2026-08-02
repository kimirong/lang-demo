"""Phase 1 · 产出1：结构化信息抽取链

核心概念：
  1. Pydantic 模型 —— 用类型声明"我想要什么样的输出"
  2. with_structured_output —— 自动生成 JSON schema 给模型，
     并把模型的输出解析回 Python 对象（不再需要手写解析）

用途：把非结构化文本 → 结构化数据，是搭 RAG / 数据清洗的基础。
"""

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from model import get_llm

llm = get_llm()

# --- 1. 定义输出结构（Pydantic）---
# 每个字段的 description 会作为提示词的一部分传给模型，写清楚很有用


class Entity(BaseModel):
    """从文本中抽取出的一个实体。"""

    name: str = Field(description="实体名称")
    type: str = Field(description="实体类型：人物 / 地点 / 机构 / 事件")
    role: str = Field(description="该实体在原文中的作用，一句话")


class ExtractionResult(BaseModel):
    """整段文本的抽取结果。"""

    entities: list[Entity] = Field(description="文本中出现的所有重要实体")
    summary: str = Field(description="用 30 字以内概括这段文本")
    language: str = Field(description="原文使用的语言，如中文、英文")


# --- 2. 绑上结构化输出 ---
# 坑：with_structured_output 默认用 response_format="json_schema"，
# DeepSeek 暂不支持这种类型。显式指定 method="function_calling"，
# 走 DeepSeek 支持的函数调用通道来输出 JSON。
structured_llm = llm.with_structured_output(ExtractionResult, method="function_calling")

# --- 3. 模板 + 链 ---
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "忠实原文抽取信息，不要编造原文没有的内容。"),
        ("human", "{text}"),
    ]
)
chain = prompt | structured_llm

# --- 4. 用一条真实文本测试 ---
news = """DeepSeek公司今天发布了一款新的推理模型，其创始人梁文锋表示，
该模型在数学和代码任务上的表现优于同级别产品。业内分析师王明认为，
这一发布可能改变国内大模型市场的竞争格局，尤其是在杭州和深圳两地
的AI初创公司之间。"""

result: ExtractionResult = chain.invoke({"text": news})

print("=" * 60)
print("抽取结果（类型化 Python 对象）")
print("=" * 60)
print(f"语言：{result.language}")
print(f"摘要：{result.summary}")
print("-" * 60)
print("实体列表：")
for e in result.entities:
    print(f"  [{e.type}] {e.name} —— {e.role}")
print("-" * 60)
print(f"result 的类型: {type(result).__name__}")
print(f"entities[0] 的类型: {type(result.entities[0]).__name__}")
print()
print(">>> 关键点：返回的是 Pydantic 对象，可直接 .属性 访问，")
print(">>> 也能 .model_dump_json() 转成 JSON 给前端/数据库。")
