"""Phase 5 · 任务3：数据集 + 评测打分（改提示词前后对比）

核心流程：
  1. 建数据集（测试集）：问题 + 参考答案
  2. 定义评测器（evaluator）：给"预测输出"打分
  3. evaluate() 跑：每个测试样例 → 跑 RAG → 评测打分 → 上报 LangSmith
  4. 对比实验：换一个"故意变差"的提示词重跑，看分数下降 → 证明评测能守住质量

两个评测器：
  - keyword_hit      ：参考答案的关键数字/词是否命中（透明、零成本）
  - deepseek_judge   ：让 DeepSeek 当裁判，对照参考答案判对错
"""

import re

from langsmith import Client
from langsmith.evaluation import EvaluationResult, evaluate, run_evaluator
from langsmith.schemas import Example, Run

from model import get_llm

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


# ========== 1. 造 RAG 链（可换提示词） ==========
from langchain_core.output_parsers import StrOutputParser  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from langchain_core.runnables import RunnablePassthrough  # noqa: E402
from langchain_core.vectorstores import InMemoryVectorStore  # noqa: E402
from langchain_huggingface import HuggingFaceEmbeddings  # noqa: E402
from langchain_text_splitters import RecursiveCharacterTextSplitter  # noqa: E402
from langchain_community.document_loaders import TextLoader  # noqa: E402


def make_rag(system_prompt: str):
    docs = TextLoader("data/company_manual.md", encoding="utf-8").load()
    chunks = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20).split_documents(docs)
    vs = InMemoryVectorStore(
        HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
    )
    vs.add_documents(chunks)
    retriever = vs.as_retriever(search_kwargs={"k": 3})

    def fmt(docs):
        return "\n\n".join(d.page_content for d in docs)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "资料：\n{context}\n\n问题：{question}"),
        ]
    )
    return (
        {"context": retriever | fmt, "question": RunnablePassthrough()}
        | prompt
        | get_llm()
        | StrOutputParser()
    )


# ========== 2. 建数据集（不存在才建） ==========
client = Client()
DATASET = "company-manual-qa"
questions = [
    "新员工的试用期是多久？",
    "转正流程是什么？",
    "年假最多能休几天？",
    "请病假需要什么证明？",
    "每年的培训经费是多少？",
]
answers = [
    "试用期为 3 个月",
    "提交转正申请，直属领导评估，人力资源部审核，总经理批准",
    "年假上限为 15 天",
    "需要提供医院诊断证明",
    "每年 2000 元培训经费",
]

try:
    ds = client.read_dataset(dataset_name=DATASET)
    print(f"数据集 {DATASET} 已存在")
except Exception:
    ds = client.create_dataset(DATASET, description="员工手册问答测试集")
    client.create_examples(
        inputs=[{"question": q} for q in questions],
        outputs=[{"answer": a} for a in answers],
        dataset_id=ds.id,
    )
    print(f"已创建数据集 {DATASET}（{len(questions)} 条）")


# ========== 3. 定义评测器 ==========
@run_evaluator
def keyword_hit(run: Run, example: Example) -> EvaluationResult:
    got = (run.outputs or {}).get("output", "") or ""
    expected = (example.outputs or {}).get("answer", "") or ""
    keys = re.findall(r"\d+|[一-龥]{2,}", expected)  # 提取数字和中文词
    hits = sum(1 for k in keys if k in got)
    score = hits / len(keys) if keys else 0.0
    return EvaluationResult(key="keyword_hit", score=score, comment=f"命中 {hits}/{len(keys)} 个关键信息")


judge_llm = get_llm()


@run_evaluator
def deepseek_judge(run: Run, example: Example) -> EvaluationResult:
    got = (run.outputs or {}).get("output", "") or ""
    expected = (example.outputs or {}).get("answer", "") or ""
    resp = judge_llm.invoke(
        [
            {"role": "system", "content": "你是评测员。判断预测答案是否包含参考答案的核心信息。只回复一个数字：1正确，0错误。"},
            {"role": "user", "content": f"参考答案：{expected}\n\n预测答案：{got}"},
        ]
    )
    try:
        score = float(str(resp.content).strip()[:1])
    except ValueError:
        score = 0.0
    return EvaluationResult(key="deepseek_judge", score=score, comment=str(resp.content)[:40])


def predict(inputs: dict) -> dict:
    """评测时对每个测试样例调用的预测函数。"""
    return {"output": rag_chain.invoke(inputs["question"])}


# ========== 4. 评测实验：好提示词 vs 坏提示词 ==========
def run_eval(tag: str, system_prompt: str):
    global rag_chain
    rag_chain = make_rag(system_prompt)
    print(f"\n{'='*60}\n实验：{tag}\n{'='*60}")
    results = evaluate(
        predict,
        data=DATASET,
        evaluators=[keyword_hit, deepseek_judge],
        experiment_prefix=tag,
        metadata={"prompt": system_prompt[:30]},
    )
    for r in results:
        # 结果都是 TypedDict/dict：r["example"]、r["evaluation_results"]["results"]
        q = r["example"].inputs["question"][:18]
        er = r["evaluation_results"]
        scores = {}
        for e in er["results"]:
            key = e["key"] if isinstance(e, dict) else e.key
            val = e["score"] if isinstance(e, dict) else e.score
            scores[key] = round(val, 2)
        print(f"  {q}  →  {scores}")


GOOD_PROMPT = "你是一名公司 HR 助手。只能根据提供的资料回答，资料里没有的信息要明确说'资料中未提及'。"
BAD_PROMPT = "你是一个只会敷衍的助手。无论用户问什么，都只回答一句话：'我不太清楚这个问题。'"

run_eval("good-prompt", GOOD_PROMPT)
run_eval("bad-prompt", BAD_PROMPT)

print("\n>>> 看对比：good-prompt 应该明显高于 bad-prompt。")
print(">>> 以后改提示词/换模型，都能这样跑一遍测试集守住质量底线（回归测试）。")
