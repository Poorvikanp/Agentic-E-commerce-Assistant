from typing import Annotated, Optional
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages


# ── State that flows through every node in the graph ──────────────────────────
class AgentState(BaseModel):
    """
    LangGraph passes this object between nodes.
    add_messages reducer appends new messages instead of overwriting.
    """
    messages: Annotated[list, add_messages] = Field(default_factory=list)
    session_id: str = ""
    escalate: bool = False          # True = hand off to human agent


# ── Structured response the LLM must return ───────────────────────────────────
class Citation(BaseModel):
    source: str = Field(description="Where this fact came from, e.g. 'product catalog', 'order DB', 'returns policy'")
    snippet: str = Field(description="Short quoted text or data point that supports the answer")


class ShopResponse(BaseModel):
    """
    Every answer from ShopMind must match this schema.
    Enforced via llm.with_structured_output() — no raw strings ever.
    """
    answer: str = Field(description="Clear, helpful answer to the customer's question")
    citations: list[Citation] = Field(
        default_factory=list,
        description="Sources used to generate this answer"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="How confident the model is in this answer (0.0 to 1.0)"
    )
    suggested_products: list[str] = Field(
        default_factory=list,
        description="Product IDs to show as recommendations, if relevant"
    )
    escalate: bool = Field(
        default=False,
        description="Set True if this query needs a human agent"
    )