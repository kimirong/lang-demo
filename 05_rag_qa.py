"""Phase 2 · RAG 检索增强问答

RAG = 检索(Retrieval) + 生成(Generation)。
流程：本地文档 → 分块 → 向量化 → 检索相关片段 → 喂给 DeepSeek 回答。

因为 DeepSeek 没有 embedding 接口，向量化用本地 sentence-transformers
模型（BAAI/bge-small-zh-v1.5，中文效果好、体积小）。

五步拆解（每一步都有打印，方便观察数据流动）：
  ① 加载文档
  ② 分块
  ③ 向量化入库
  ④ 检索
  ⑤ 拼提示词 + 回答
"""

from langchain_community.document_loaders import TextLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from model import get_llm

# ========== ① 加载文档 ==========
loader = TextLoader("data/company_manual.md", encoding="utf-8")
docs = loader.load()
print(f"① 加载文档：共 {len(docs)} 个文档，总字符数 {len(docs[0].page_content)}")

# ========== ② 分块 ==========
# chunk_size 每块字符数，chunk_overlap 相邻块重叠，避免语义被切断
splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
chunks = splitter.split_documents(docs)
print(f"② 分块：切成 {len(chunks)} 个片段（块大小约 200 字，重叠 20 字）")

# ========== ③ 向量化入库 ==========
# 注：BGE 官方建议检索 query 加"指令前缀"来提效，
# 但新版 langchain-huggingface 已移除 query_instruction 参数，
# 这里保持简洁不处理；本 demo 检索质量已足够。
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
vector_store = InMemoryVectorStore(embeddings)
vector_store.add_documents(chunks)
print("③ 向量化：每个片段变成向量，已存入内存向量库")

# ========== ④ 检索 ==========
retriever = vector_store.as_retriever(search_kwargs={"k": 3})

question = "新员工试用期多久？转正要走什么流程？"
hit_docs = retriever.invoke(question)
print(f"\n④ 检索 top-{len(hit_docs)}（问题：{question}）")
print("-" * 60)
for i, doc in enumerate(hit_docs, 1):
    print(f"  片段 {i}: {doc.page_content.replace(chr(10), ' ')[:80]}...")
print("-" * 60)


def format_docs(docs):
    """把检索到的多个 Document 拼成一段文本，作为提示词里的"资料"。"""
    return "\n\n".join(doc.page_content for doc in docs)


# ========== ⑤ RAG 链：检索 → 拼提示词 → DeepSeek → 答案 ==========
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一名公司 HR 助手。只能根据提供的资料回答；"
            "资料里没有的信息要明确说'资料中未提及'，不要编造。",
        ),
        ("human", "资料：\n{context}\n\n问题：{question}"),
    ]
)

rag_chain = (
    # 并行计算两个键：context 走"检索→拼文本"，question 原样透传
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | get_llm()
    | StrOutputParser()
)

print(f"\n⑤ DeepSeek 基于检索结果回答：\n{question}\n")
print("=" * 60)
print(rag_chain.invoke(question))
print("=" * 60)
