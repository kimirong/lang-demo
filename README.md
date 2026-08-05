# LangChain / LangGraph / LangSmith 实战学习仓库

> 🌐 **English version**: [README.en.md](README.en.md)

> 用 **DeepSeek** 模型，从零到一、**项目驱动**地学习 LangChain 三件套的完整学习仓库。
> 每个阶段都有可运行的脚本，代码里中文注释讲解每一行在做什么。

**这是一个学习仓库** —— 14 个脚本按阶段排布，跟着跑一遍就能掌握：
**接模型 → 结构化输出 → 工具调用 → RAG → 手搓 Agent → 记忆 → 多 Agent 协作 → 观测评测**。

---

## ✨ 特色

- 🎯 **项目驱动**：不是空讲概念，每阶段产出可运行脚本
- 🧠 **手搓核心机制**：Phase 3 用 LangGraph 亲手复现 `create_agent` 的循环，拒绝黑盒
- 🐍 **DeepSeek 实战**：完整展示 OpenAI 兼容接口接入、结构化输出的兼容性坑
- 📊 **生产思维**：RAG 的 SQLite 持久化、多轮记忆、人工审批、LangSmith 评测回归
- 🇨🇳 **中文讲解**：注释与文档全中文，适合中文学习者

---

## 📚 学习路线

| 阶段 | 主题 | 产出 |
|---|---|---|
| Phase 0 | 环境搭建 + DeepSeek 接入 | `01` |
| Phase 1 | LangChain 核心（模板/LCEL/结构化输出/工具） | `02` `03` `04` |
| Phase 2 | RAG 检索增强（内存版 + SQLite 持久化版） | `05` `06` |
| Phase 3 | LangGraph 入门（手搓 agent 循环 / 多轮记忆） | `07` `08` `09` |
| Phase 4 | LangGraph 进阶（人工审批 / 多 Agent / 长期记忆） | `10` `11` `12` |
| Phase 5 | LangSmith（自动埋点 / 读 trace / 评测回归） | `13` `14` |
| Phase 6 | 综合实战：客服 agent 打包成 FastAPI | `customer_service/` `app.py` `test_api.py` |
| Phase 7 | 前端实战：Vue 3 客服控制台 | `frontend/` |

> 📖 完整计划、每阶段概念、踩坑速查见 **[LEARNING_PLAN.md](LEARNING_PLAN.md)**

---

## 🛠 环境要求

- **Python 3.12**（推荐 Homebrew 版；若用 sqlite-vec 需要 sqlite3 支持扩展加载，见 [踩坑表](#-踩坑速查)）
- **DeepSeek API key**（[platform.deepseek.com](https://platform.deepseek.com) 注册）
- LangSmith key（可选，仅 Phase 5 需要）

## 🚀 快速开始

```bash
# 1. 克隆并进入
git clone <本仓库地址>
cd lang-demo

# 2. 创建虚拟环境并安装依赖
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. 配置密钥
cp .env.example .env
# 编辑 .env，填入你的 DEEPSEEK_API_KEY

# 4. 运行（从 Phase 0 开始）
.venv/bin/python 01_hello_deepseek.py
```

> ⚠️ **注意**：embedding 模型 `BAAI/bge-small-zh-v1.5` 首次运行会自动下载（约 100MB）。
> 国内网络可设置 `HF_ENDPOINT=https://hf-mirror.com`；已缓存后脚本自动走离线模式。
> 所有脚本请用 `.venv/bin/python xxx.py` 直接运行，无需额外环境变量前缀。

## 📁 目录结构

| 文件 | 阶段 | 内容 |
|---|---|---|
| `model.py` | 公共 | DeepSeek 模型工厂 + 环境变量统一处理（**脚本必须最先 import**） |
| `01_hello_deepseek.py` | P0 | invoke / stream / 多轮对话 |
| `02_prompt_and_lcel.py` | P1 | 提示词模板 + LCEL 管道 |
| `03_structured_extraction.py` | P1 | Pydantic 结构化信息抽取 |
| `04_single_tool_agent.py` | P1 | 单工具 agent（@tool + create_agent） |
| `05_rag_qa.py` | P2 | RAG（内存向量库版） |
| `06_rag_sqlite.py` | P2 | RAG（SQLite + sqlite-vec 持久化版） |
| `07_graph_basics.py` | P3 | StateGraph 基础：State/节点/边/条件边 |
| `08_handrolled_agent.py` | P3 | 手搓"思考→行动→观察"循环 |
| `09_memory_checkpoint.py` | P3 | checkpointer + thread_id 多轮记忆 |
| `10_hitl.py` | P4 | Human-in-the-loop 人工审批 |
| `11_supervisor_multiagent.py` | P4 | supervisor 多 Agent 协作 |
| `12_longterm_memory.py` | P4 | InMemoryStore 长期记忆 |
| `13_read_traces.py` | P5 | 用 SDK 读 trace 树、定位问题 |
| `14_evaluate.py` | P5 | 数据集 + 评测，好/坏提示词对比 |
| `customer_service/` | P6 | 客服业务包：RAG 检索 / 工具 / agent 图 |
| `app.py` | P6 | FastAPI 入口（/health /chat /approve /history） |
| `test_api.py` | P6 | 端到端测试（11 项断言全过） |
| `frontend/` | P7 | Vue 3 前端控制台（聊天 / 会话历史 / 下单审批） |
| `data/company_manual.md` | 测试 | 测试知识库（虚构员工手册） |

### 🚀 启动客服 API（Phase 6）

```bash
.venv/bin/uvicorn app:app --port 8000
# 快速验证
.venv/bin/python test_api.py          # 端到端测试
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" \
     -d '{"session_id":"demo-1","message":"试用期多久？"}'
```

### 🖥 前端控制台（Phase 7）

```bash
# 1. 先启动后端（见上）
.venv/bin/uvicorn app:app --port 8000

# 2. 启动前端（需 Node 18+ / pnpm）
cd frontend
pnpm install
pnpm dev            # 打开 http://localhost:5173

# 生产构建（可选）
pnpm build          # 产物在 frontend/dist/
```

- 前端所有请求走 `/api/*`，由 Vite 开发代理转发到 `127.0.0.1:8000`，**后端零改动**
- 支持：多会话聊天、会话历史（localStorage 记忆）、**下单人工审批**（批准/拒绝按钮）
- 下单时后端返回 `pending_approval` → 前端渲染订单审批卡片 → 批准/拒绝后展示结果

## ⚠️ 踩坑速查

| 坑 | 解法 |
|---|---|
| DeepSeek 结构化输出报 400 | `with_structured_output(..., method="function_calling")` |
| DeepSeek 没有 embedding 接口 | 用本地 `bge-small-zh-v1.5` |
| huggingface.co 下载超时 | `HF_ENDPOINT=https://hf-mirror.com` |
| 模型已缓存仍联网挂起 | `HF_HUB_OFFLINE` 必须在 huggingface_hub import 前设置（已内置在 model.py） |
| python.org 的 sqlite3 无法加载扩展 | 换 Homebrew Python 3.12 |
| SQLite 跨线程报错 | 连接加 `check_same_thread=False` |
| 多 Agent 报 "tool_calls 后必须有 ToolMessage" | 员工产出包成 ToolMessage 回填给主管 |

完整版见 [LEARNING_PLAN.md](LEARNING_PLAN.md) 第六节。

---

## 🤝 说明

- 本项目用于学习与交流，请使用**你自己的 API key**
- 若对你有所帮助，欢迎 ⭐ Star
- 有更好的讲解方式，欢迎提 Issue / PR
