# LangChain / LangGraph / LangSmith Hands-On Learning Repository

> A complete, **project-driven** learning repository for the LangChain trilogy, built from scratch with the **DeepSeek** model.
> Every phase ships a runnable script, with Chinese comments explaining what each line does.

**This is a learning repository** — 14 scripts arranged by phase. Follow along and you'll master:
**connecting a model → structured output → tool calling → RAG → building an agent from scratch → memory → multi-agent collaboration → observability & evaluation**.

- 🌐 **[中文版 (Chinese)](README.md)**

---

## ✨ Highlights

- 🎯 **Project-driven**: not just theory — every phase produces runnable scripts
- 🧠 **Build core mechanics by hand**: Phase 3 hand-rolls the `create_agent` loop with LangGraph — no black boxes
- 🐍 **DeepSeek in practice**: full walkthrough of the OpenAI-compatible integration, including structured-output compatibility gotchas
- 📊 **Production mindset**: SQLite-persisted RAG, multi-turn memory, human-in-the-loop approval, LangSmith evaluation regression
- 🇨🇳 **Chinese explanations**: all comments and docs are in Chinese, ideal for Chinese-speaking learners

---

## 📚 Learning Roadmap

| Phase | Topic | Deliverable |
|---|---|---|
| Phase 0 | Environment setup + DeepSeek integration | `01` |
| Phase 1 | LangChain core (prompts / LCEL / structured output / tools) | `02` `03` `04` |
| Phase 2 | RAG (in-memory + SQLite-persisted versions) | `05` `06` |
| Phase 3 | LangGraph basics (hand-rolled agent loop / multi-turn memory) | `07` `08` `09` |
| Phase 4 | LangGraph advanced (human approval / multi-agent / long-term memory) | `10` `11` `12` |
| Phase 5 | LangSmith (auto tracing / reading traces / evaluation regression) | `13` `14` |
| Phase 6 | Capstone: customer-service agent packaged as FastAPI | `customer_service/` `app.py` `test_api.py` |
| Phase 7 | Frontend: Vue 3 customer-service console | `frontend/` |

> 📖 Full plan, per-phase concepts, and a gotcha cheat-sheet live in **[LEARNING_PLAN.md](LEARNING_PLAN.md)**

---

## 🛠 Environment Requirements

- **Python 3.12** (Homebrew build recommended; sqlite-vec requires a sqlite3 that supports loading extensions — see the [Gotchas](#-gotchas) section)
- **DeepSeek API key** (sign up at [platform.deepseek.com](https://platform.deepseek.com))
- LangSmith key (optional — only needed for Phase 5)

## 🚀 Quick Start

```bash
# 1. Clone and enter
git clone <this-repo-url>
cd lang-demo

# 2. Create a virtual environment and install dependencies
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. Configure secrets
cp .env.example .env
# edit .env and fill in your DEEPSEEK_API_KEY

# 4. Run (starting from Phase 0)
.venv/bin/python 01_hello_deepseek.py
```

> ⚠️ **Note**: the embedding model `BAAI/bge-small-zh-v1.5` downloads automatically on first run (~100MB).
> Behind a restricted network, set `HF_ENDPOINT=https://hf-mirror.com`; once cached, scripts automatically run offline.
> Always run scripts with `.venv/bin/python xxx.py` directly — no extra env-var prefixes needed.

## 📁 Directory Structure

| File | Phase | Content |
|---|---|---|
| `model.py` | shared | DeepSeek model factory + centralized env setup (**must be the first import in every script**) |
| `01_hello_deepseek.py` | P0 | invoke / stream / multi-turn conversation |
| `02_prompt_and_lcel.py` | P1 | prompt templates + LCEL pipelines |
| `03_structured_extraction.py` | P1 | Pydantic structured extraction |
| `04_single_tool_agent.py` | P1 | single-tool agent (`@tool` + `create_agent`) |
| `05_rag_qa.py` | P2 | RAG (in-memory vector store) |
| `06_rag_sqlite.py` | P2 | RAG (SQLite + sqlite-vec, persisted) |
| `07_graph_basics.py` | P3 | StateGraph basics: State / nodes / edges / conditional edges |
| `08_handrolled_agent.py` | P3 | hand-rolled "think → act → observe" loop |
| `09_memory_checkpoint.py` | P3 | checkpointer + `thread_id` multi-turn memory |
| `10_hitl.py` | P4 | Human-in-the-loop approval |
| `11_supervisor_multiagent.py` | P4 | supervisor multi-agent collaboration |
| `12_longterm_memory.py` | P4 | InMemoryStore long-term memory |
| `13_read_traces.py` | P5 | read trace trees with the SDK, locate problems |
| `14_evaluate.py` | P5 | dataset + evaluation, good vs bad prompt comparison |
| `customer_service/` | P6 | customer-service package: RAG retrieval / tools / agent graph |
| `app.py` | P6 | FastAPI entry (`/health` `/chat` `/approve` `/history`) |
| `test_api.py` | P6 | end-to-end tests (all 11 assertions pass) |
| `frontend/` | P7 | Vue 3 console (chat / session history / order approval) |
| `data/company_manual.md` | test | test knowledge base (fictional employee handbook) |

### 🚀 Start the Customer-Service API (Phase 6)

```bash
.venv/bin/uvicorn app:app --port 8000
# quick verification
.venv/bin/python test_api.py          # end-to-end tests
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" \
     -d '{"session_id":"demo-1","message":"试用期多久？"}'
```

### 🖥 Frontend Console (Phase 7)

```bash
# 1. Start the backend first (see above)
.venv/bin/uvicorn app:app --port 8000

# 2. Start the frontend (requires Node 18+ / pnpm)
cd frontend
pnpm install
pnpm dev            # open http://localhost:5173

# production build (optional)
pnpm build          # output in frontend/dist/
```

- The frontend calls everything through `/api/*`, which the Vite dev proxy forwards to `127.0.0.1:8000` — **zero backend changes**
- Features: multi-session chat, session history (remembered in localStorage), **visual order approval** (approve / reject buttons)
- On checkout, the backend returns `pending_approval` → the frontend renders an order-approval card → approve/reject → shows the result

## ⚠️ Gotchas

| Pitfall | Fix |
|---|---|
| DeepSeek structured output returns 400 | `with_structured_output(..., method="function_calling")` |
| DeepSeek has no embedding endpoint | use local `bge-small-zh-v1.5` |
| huggingface.co download times out | `HF_ENDPOINT=https://hf-mirror.com` |
| model cached but still hangs trying to reach the network | `HF_HUB_OFFLINE` must be set **before** `huggingface_hub` is imported (already built into `model.py`) |
| python.org's sqlite3 can't load extensions | switch to Homebrew Python 3.12 |
| SQLite cross-thread error | add `check_same_thread=False` to the connection |
| Multi-agent "tool_calls must be followed by a ToolMessage" | wrap the worker's output in a ToolMessage and feed it back to the supervisor |

The full version is in section 6 of [LEARNING_PLAN.md](LEARNING_PLAN.md).

---

## 🤝 Notes

- This project is for learning and sharing — please use **your own API key**
- If it helped you, a ⭐ Star is always welcome
- Better explanations? Feel free to open an Issue / PR
