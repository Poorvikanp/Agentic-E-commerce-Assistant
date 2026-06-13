"""
main.py — FastAPI backend for ShopMind
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid

from agent.graph import run_agent

app = FastAPI(title="ShopMind API", version="1.0.0")

# Allow React frontend on localhost:5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response schemas ─────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: str = ""


class ChatResponse(BaseModel):
    answer: str
    tool_calls_made: list[str]
    session_id: str
    escalate: bool


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ShopMind API is running"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Main chat endpoint.
    Receives a user message, runs it through the LangGraph agent,
    returns a structured response.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = req.session_id or str(uuid.uuid4())

    try:
        result = run_agent(req.message, session_id)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products")
def list_products():
    """Return all products — used by frontend to display catalog."""
    import json
    from pathlib import Path
    with open(Path(__file__).parent / "data/products.json") as f:
        return json.load(f)