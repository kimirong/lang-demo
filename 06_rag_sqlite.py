"""Phase 2 完善 · RAG + SQLite 持久化向量库

相比 05 的内存版（InMemoryVectorStore），核心升级：
  - 向量存入本地 SQLite 文件（data/vector_store.db），重启不丢
  - 二次运行直接读库，不再重复向量化（幂等）

底层扩展：sqlite-vec（SQLite 的向量检索扩展，LangChain 官方封装 SQLiteVec）。
"""

import os
import sqlite3

import sqlite_vec
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import SQLiteVec
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from model import get_llm

# ========== 配置 ==========
DB_FILE = "data/vector_store.db"
TABLE = "company_manual"

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")

# 手动建连接：复制 SQLiteVec.create_connection 的步骤，但额外加
# check_same_thread=False —— LCEL 并行分支({context, question})会开子线程检索，
# 默认连接不允许跨线程用，会抛 ProgrammingError。
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
conn.row_factory = sqlite3.Row
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)

vector_store = SQLiteVec(table=TABLE, connection=conn, embedding=embeddings, db_file=DB_FILE)
vector_store.create_table_if_not_exists()

# ========== 幂等入库：只有库为空时才重新向量化 ==========
def stored_count() -> int:
    """查 SQLite 表里已存了几条向量。"""
    conn = sqlite3.connect(DB_FILE)
    try:
        n = conn.execute(f'SELECT COUNT(*) FROM "{TABLE}"').fetchone()[0]
    except sqlite3.OperationalError:
        n = 0
    conn.close()
    return n

if stored_count() == 0:
    print("首次运行：加载 → 分块 → 向量化入库 ...")
    docs = TextLoader("data/company_manual.md", encoding="utf-8").load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
    chunks = splitter.split_documents(docs)
    vector_store.add_texts(
        texts=[d.page_content for d in chunks],
        metadatas=[d.metadata for d in chunks],
    )
    print(f"  已入库 {stored_count()} 个向量片段")
else:
    print(f"检测到数据库已有 {stored_count()} 个向量，跳过向量化，直接读库检索")

print(f"数据库文件：{DB_FILE}（{os.path.getsize(DB_FILE) / 1024:.1f} KB）")

# ========== 检索 ==========
retriever = vector_store.as_retriever(search_kwargs={"k": 3})

question = "年假怎么算？最多能休几天？"
hit_docs = retriever.invoke(question)
print(f"\n检索 top-{len(hit_docs)}（问题：{question}）")
print("-" * 60)
for i, doc in enumerate(hit_docs, 1):
    print(f"  片段 {i}: {doc.page_content.replace(chr(10), ' ')[:80]}...")
print("-" * 60)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# ========== 问答链 ==========
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
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | get_llm()
    | StrOutputParser()
)

print(f"\nDeepSeek 基于 SQLite 检索结果回答：\n{question}\n")
print("=" * 60)
print(rag_chain.invoke(question))
print("=" * 60)
print("\n>>> 验证持久化：再跑一次本脚本，会看到'直接读库，跳过向量化'。")
