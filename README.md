# ShopMind 🛍️ — Agentic E-commerce Assistant

An AI shopping assistant built with **LangGraph + LangChain + Groq** that handles real customer queries using a multi-tool agent — not just RAG.

🛠 **LangGraph · LangChain · Groq · FAISS · FastAPI · React · LangSmith**

## About

ShopMind is a production-style AI shopping assistant that goes beyond basic RAG. Instead of a simple retrieve-and-answer pipeline, it uses a LangGraph StateGraph where the LLM autonomously decides which tool to invoke based on the customer's intent. Order queries are handled deterministically via a DB lookup tool — the LLM never guesses order status. Product queries use FAISS semantic search. Policy questions use RAG over store documents. All responses are Pydantic-validated structured objects with citations. Agent traces and tool routing accuracy are tracked via LangSmith.

## What makes this different from basic RAG

| Feature | Basic RAG | ShopMind |
|---|---|---|
| Architecture | Retrieve → Answer | LangGraph StateGraph agent |
| Order queries | Hallucinated | Deterministic DB lookup via tool |
| LLM output | Raw string | Pydantic structured output |
| Observability | None | LangSmith traces + eval scores |
| Tool selection | Manual | LLM decides which tool to call |

## Agent Tools

| Tool | Trigger | Method |
|---|---|---|
| `search_products` | Product questions | FAISS semantic search |
| `check_order` | Order status | Deterministic JSON DB lookup |
| `get_policy` | Return/shipping questions | Keyword-routed policy RAG |
| `recommend_bundle` | "What goes with X?" | Rule-based upsell logic |

## Architecture

```
User → FastAPI → LangGraph Agent → [Tool selection by LLM]
                                    ├── search_products (FAISS)
                                    ├── check_order (DB)
                                    ├── get_policy (RAG)
                                    └── recommend_bundle (rules)
                       ↓
              Structured output (Pydantic)
                       ↓
              React frontend with citation badges
```

## Evaluation & Observability

Ran a 20-case LangSmith evaluation suite testing tool-routing correctness across all 4 tools plus escalation handling.

**Result: 90% tool-routing accuracy (18/20)**

<img width="1360" height="583" alt="Screenshot (522)" src="https://github.com/user-attachments/assets/16339dbe-7f16-4a83-84fc-cd0885a31ae9" />



Every agent run is traced end-to-end — full visibility into which tool was called, latency per step, and the final structured output.

## Stack

- **LangGraph** — agent orchestration (StateGraph)
- **LangChain** — tools, LLM binding, prompt templates
- **Groq** — free LLM inference (llama-3.1-8b-instant)
- **FAISS** — semantic product search
- **sentence-transformers** — embeddings (all-MiniLM-L6-v2)
- **FastAPI** — REST backend
- **React** — chat frontend with citation badges
- **LangSmith** — tracing and evaluation

## Setup

### 1. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Add API keys

Create `backend/.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=shopmind
```

Get free keys at [console.groq.com](https://console.groq.com) and [smith.langchain.com](https://smith.langchain.com).

### 3. Run backend

```bash
cd backend
uvicorn main:app --reload
# API running at http://localhost:8000
```

### 4. Run frontend

```bash
cd frontend
npm install
npm run dev
# UI at http://localhost:5173
```

### 5. Run evals

```bash
cd backend
python eval.py
# Results at smith.langchain.com
```

## Example queries

- "Do you have running shoes under ₹3000?"
- "Where is my order ORD-1002?"
- "What is your return policy on yoga mats?"
- "I'm buying the hiking backpack, what else should I get?"

## Project Structure

```
shopmind/
├── backend/
│   ├── main.py              # FastAPI app + /chat endpoint
│   ├── eval.py               # LangSmith evaluation script
│   ├── agent/
│   │   ├── graph.py          # LangGraph StateGraph (agent core)
│   │   ├── state.py          # AgentState + ShopResponse models
│   │   ├── tools.py          # 4 LangChain tools
│   │   └── prompts.py        # system prompt
│   └── data/
│       ├── products.json
│       ├── orders.json
│       └── policies/
└── frontend/
    └── src/
        ├── App.jsx
        ├── ChatWindow.jsx
        └── CitationBadge.jsx
```


