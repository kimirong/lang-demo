"""RAG 检索器：加载/构建《员工手册》SQLite 向量库，提供检索。

设计要点：
  - 模块级单例（_get_store）：应用启动时构建一次，之后所有请求复用，
    避免每个请求都重新向量化。
  - 幂等索引：向量库为空时才从 Markdown 重建，重复启动不重复嵌入。
  - 连接 check_same_thread=False：LangChain/API 线程池里跨线程用（06 踩过的坑）。
"""

import os
import sqlite3

import sqlite_vec
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import SQLiteVec
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

DB_FILE = "data/vector_store.db"
TABLE = "company_manual"
SOURCE = "data/company_manual.md"  # 测试知识库：虚构员工手册

_embeddings: HuggingFaceEmbeddings | None = None
_vector_store: SQLiteVec | None = None


def _get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
    return _embeddings


def _store_count() -> int:
    """向量库里已存几条向量。"""
    conn = sqlite3.connect(DB_FILE)
    try:
        return conn.execute(f'SELECT COUNT(*) FROM "{TABLE}"').fetchone()[0]
    except sqlite3.OperationalError:
        return 0
    finally:
        conn.close()


def _ensure_indexed() -> None:
    """幂等索引：库空才重建，避免重复向量化。"""
    if _store_count() > 0:
        return
    print(f"首次运行：索引 {SOURCE} → SQLite 向量库 ...")
    docs = TextLoader(SOURCE, encoding="utf-8").load()
    chunks = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20).split_documents(docs)
    _vector_store.add_texts(
        texts=[d.page_content for d in chunks],
        metadatas=[d.metadata for d in chunks],
    )
    print(f"  已索引 {_store_count()} 个片段")


def _get_store() -> SQLiteVec:
    global _vector_store
    if _vector_store is None:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        _vector_store = SQLiteVec(
            table=TABLE, connection=conn, embedding=_get_embeddings(), db_file=DB_FILE
        )
        _vector_store.create_table_if_not_exists()
        _ensure_indexed()
    return _vector_store


def retrieve(query: str, k: int = 3) -> str:
    """语义检索员工手册，返回 top-k 片段拼成的文本（供工具返回给模型）。"""
    docs = _get_store().similarity_search(query, k=k)
    if not docs:
        return "（未在《员工手册》中检索到相关内容）"
    return "\n\n".join(d.page_content for d in docs)
