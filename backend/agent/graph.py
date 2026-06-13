"""
graph.py — LangGraph StateGraph for ShopMind

Flow:
  START
    └─► llm_node        (LLM decides: answer directly OR call a tool)
          ├─► tool_node  (LangChain ToolNode executes the chosen tool)
          │     └─► llm_node  (LLM reads tool result, forms final answer)
          └─► END        (if no tool needed)

The LLM is bound with all tools via llm.bind_tools().
Conditional edge: if the last message has tool_calls → go to tool_node, else END.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from agent.state import AgentState
from agent.tools import ALL_TOOLS
from agent.prompts import prompt

load_dotenv()


# ── Build LLM ─────────────────────────────────────────────────────────────────
def get_llm():
    return ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.1,        # low temp = more deterministic, less hallucination
        max_tokens=1024,
    )


# ── Node: LLM decides what to do ──────────────────────────────────────────────
def llm_node(state: AgentState) -> dict:
    """
    Core reasoning node.
    - Binds all tools to the LLM so it can choose which to call.
    - Uses the system prompt from prompts.py.
    - Returns updated messages (either a tool_call or a final answer).
    """
    llm = get_llm()
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    # Format messages through the prompt template
    formatted = prompt.invoke({"messages": state.messages})

    response = llm_with_tools.invoke(formatted)
    return {"messages": [response]}


# ── Node: Execute whichever tool the LLM chose ────────────────────────────────
tool_node = ToolNode(ALL_TOOLS)


# ── Build the graph ───────────────────────────────────────────────────────────
def build_graph():
    """
    Constructs and compiles the LangGraph StateGraph.

    Graph structure:
        START → llm_node → [tools_condition] → tool_node → llm_node → END
                                              ↘ END (if no tool call)
    """
    builder = StateGraph(AgentState)

    # Add nodes
    builder.add_node("llm_node", llm_node)
    builder.add_node("tool_node", tool_node)

    # Entry point
    builder.add_edge(START, "llm_node")

    # Conditional routing:
    # tools_condition checks if the last AI message has tool_calls
    # If yes → "tool_node", if no → END
    builder.add_conditional_edges(
        "llm_node",
        tools_condition,                        # built-in LangGraph condition
        {"tools": "tool_node", END: END}
    )

    # After tool execution, always go back to LLM to form final answer
    builder.add_edge("tool_node", "llm_node")

    return builder.compile()


# ── Public interface ──────────────────────────────────────────────────────────
graph = build_graph()


def run_agent(user_message: str, session_id: str = "default") -> dict:
    """
    Entry point called by FastAPI.
    Returns a dict with answer, citations, confidence, etc.
    """
    initial_state = AgentState(
        messages=[HumanMessage(content=user_message)],
        session_id=session_id
    )

    final_state = graph.invoke(initial_state)

    # Get last AI message
    last_msg = final_state["messages"][-1]
    answer_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    # Collect tool calls made during this run (for citations)
    tool_calls_made = []
    for msg in final_state["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls_made.append(tc.get("name", "unknown_tool"))

    return {
        "answer": answer_text,
        "tool_calls_made": tool_calls_made,
        "session_id": session_id,
        "escalate": final_state.get("escalate", False)
    }