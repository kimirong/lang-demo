# LangChain / LangGraph / LangSmith 学习计划与进度

> 项目：`lang-demo` · 语言：Python · 模型：DeepSeek（OpenAI 兼容接口）
> 目标：能上手搭真实应用（项目驱动，每阶段有可运行产出）

---

## 一、全局心智模型

三个工具不是并列的库，而是**一层叠一层**的关系：

```
┌─────────────────────────────────────────────────────┐
│  LangSmith —— 观测台：每个调用自动留 trace，可评测可回放 │  ← 罩住全局
├─────────────────────────────────────────────────────┤
│  LangGraph —— 编排引擎：状态 + 节点 + 边，循环/分支/记忆  │  ← 控制"流程"
├─────────────────────────────────────────────────────┤
│  LangChain —— 组件库：模型/提示词/解析器/工具/向量检索     │  ← 提供"零件"
└─────────────────────────────────────────────────────┘
```

| 工具 | 回答的问题 | 类比 |
|---|---|---|
| LangChain | 怎么用 DeepSeek 干活？ | 零件库 |
| LangGraph | 会循环、有记忆的 agent 怎么编排？ | 流水线图纸 |
| LangSmith | 它跑得好不好？出错去哪看？怎么批量测？ | 仪表盘 + 质检台 |

---

## 二、技术栈与环境（重要，别再踩）

- **Python 3.12（Homebrew `/opt/homebrew/bin/python3.12`）**，venv 在 `.venv/`
  - 原因：python.org 的 Python 3.10 编译时禁用了 SQLite 扩展加载，sqlite-vec 无法使用
- **版本**：langchain 1.3.14 · langgraph 1.2.10 · langsmith 0.10.15 · sqlite-vec 0.1.9
- **DeepSeek 接入**：`ChatOpenAI(model="deepseek-chat", base_url="https://api.deepseek.com")`，公共工厂在 `model.py:get_llm()`
- **API key**：`.env` 的 `DEEPSEEK_API_KEY`（已 gitignore）
- **Embedding**：本地 `BAAI/bge-small-zh-v1.5`（DeepSeek 没有 embedding 接口），已缓存

**运行注意事项**：
- 所有脚本直接 `.venv/bin/python xxx.py` 即可，**不需要加任何前缀**
- `model.py` **必须在脚本第一个 import** —— 它负责设置 `HF_HUB_OFFLINE` 离线变量，而 `huggingface_hub` 在 import 时就缓存该值，设晚了模型会联网挂起几分钟
- 新增脚本时，第一行 import 写 `from model import get_llm`（见 05/06/12 的教训）

---

## 三、分支管理约定

- 每个学习阶段一个分支 `phase-N`，下一个阶段的分支必须等上一阶段正式完成后，基于其完成态开出
- 每阶段完成后合并回 `main`，`main` 始终是最新稳定版
- 当前最新稳定版：`main` = Phase 4

---

## 四、学习进度总览

| 阶段 | 主题 | 状态 | 产出文件 |
|---|---|---|---|
| Phase 0 | 环境搭建 + 首条对话 | ✅ | `01_hello_deepseek.py` |
| Phase 1 | LangChain 核心 | ✅ | `02` `03` `04` |
| Phase 2 | RAG 检索增强 | ✅ | `05`（内存版）`06`（SQLite版） |
| Phase 3 | LangGraph 入门 | ✅ | `07` `08` `09` |
| Phase 4 | LangGraph 进阶 | ✅ | `10` `11` `12` |
| Phase 5 | LangSmith 观测与评测 | ✅ | `13` `14` |
| Phase 6 | 综合实战项目 | ⬜ 下一步 | — |

---

## 五、各阶段详情

### Phase 0 · 环境搭建 ✅
- 产出：`01_hello_deepseek.py`
- 学会：`ChatOpenAI` 接入 DeepSeek、`invoke` / `stream` / 多轮消息

### Phase 1 · LangChain 核心 ✅
- `02_prompt_and_lcel.py` — 消息模板 `ChatPromptTemplate`、LCEL `|` 管道、`StrOutputParser`
- `03_structured_extraction.py` — Pydantic 定义输出、`with_structured_output` 返回类型化对象
- `04_single_tool_agent.py` — `@tool` 装饰器、`create_agent`、工具调用循环
- 核心理解：LCEL 任何"可运行对象"都能用 `|` 组合，自动继承 invoke/stream/batch

### Phase 2 · RAG 检索增强 ✅
- `05_rag_qa.py` — 内存向量库版：加载→分块→向量化→检索→拼提示词
- `06_rag_sqlite.py` — SQLite 持久化版：`sqlite-vec` 扩展 + 幂等入库
- 核心理解：RAG = 检索 + 生成；DeepSeek 没 embedding → 本地 bge
- 数据：`data/company_manual.md`（测试文档）；`data/vector_store.db`（已 gitignore）

### Phase 3 · LangGraph 入门 ✅
- `07_graph_basics.py` — State / 节点 / 边 / 条件边 / 规约器
- `08_handrolled_agent.py` — 手搓"思考→行动→观察"循环，看透 `create_agent`
- `09_memory_checkpoint.py` — `checkpointer` + `thread_id` 多轮记忆
- 核心理解：**agent = 图上的一条环**；`thread_id` = 会话 id

### Phase 4 · LangGraph 进阶 ✅
- `10_hitl.py` — `interrupt()` 暂停 + `Command(resume=...)` 恢复，人工审批
- `11_supervisor_multiagent.py` — supervisor 模式：主管用工具调用路由，员工产出作为 ToolMessage 回填
- `12_longterm_memory.py` — `InMemoryStore` + 语义索引，跨会话长期记忆
- 记忆体系对比：

### Phase 5 · LangSmith 观测与评测 ✅
- 配置：`.env` 里 `LANGSMITH_API_KEY` + `LANGSMITH_TRACING=true`，加代理（HTTP 代理即可，socks5 需 socksio）
- `13_read_traces.py` — 用 SDK 拉取 trace 树，看结构/耗时/token，定位最慢子步骤
- `14_evaluate.py` — 建数据集 + `@run_evaluator` 自定义评测器，跑 good vs bad 提示词对比实验
- 核心理解：自动埋点零代码；评测器（keyword_hit 脆弱 vs LLM judge 语义）是质量守门员；改提示词前后跑测试集 = 回归测试
  ```
  短期记忆  thread_id + checkpointer  → 这一场对话
  长期记忆  InMemoryStore + namespace  → 这个人一直记得什么
  ```

---

## 六、踩过的坑速查表

| 坑 | 现象 | 解法 |
|---|---|---|
| DeepSeek 结构化输出 | 默认 json_schema 报 400 | `with_structured_output(..., method="function_calling")` |
| DeepSeek 无 embedding | 没有向量接口 | 本地 `bge-small-zh-v1.5` |
| huggingface.co 无法直连 | 模型下载超时 | `HF_ENDPOINT=https://hf-mirror.com` |
| 模型缓存仍联网挂起 | `HuggingFaceEmbeddings` 卡几分钟 | `HF_HUB_OFFLINE=1` 且**必须在 huggingface_hub import 前**设置（model.py 首个 import） |
| python.org 的 sqlite3 | 无 `enable_load_extension` | 换 Homebrew Python 3.12 |
| SQLite 跨线程 | LCEL 并行分支报 ProgrammingError | 连接加 `check_same_thread=False` |
| interrupt 的 payload | 在 `get_state().values` 取不到 | 在 `invoke()` 返回值的 `__interrupt__` 键 |
| 多 agent 工具协议 | "tool_calls 后必须有 ToolMessage" | 员工回答包成 ToolMessage 回填给主管 |

---

## 七、下一步：Phase 6 — 综合实战项目 🏆

前五个阶段学完了 LangChain / LangGraph / LangSmith 的完整能力，最后把它们拼成一个可交付的应用。

**项目设想：「DeepSeek 智能客服助手」**
- RAG 知识库（员工手册）→ 回答业务问题
- 计算工具 → 处理数值
- 多轮记忆（thread_id + checkpointer）→ 记住上下文
- 人工确认（interrupt）→ 关键操作需审批
- LangSmith → 全程监控 + 评测守护
- 最后打包成 API 服务（FastAPI / LangServe），真正跑起来被调用

> 在正式编写代码前，建议先用 EnterPlanMode 规划项目结构与实现步骤。
