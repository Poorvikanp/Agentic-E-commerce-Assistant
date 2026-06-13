"""
eval.py — LangSmith evaluation for ShopMind
Run: python eval.py
Keep uvicorn running in another terminal before running this.
"""

import os
import time
from dotenv import load_dotenv
load_dotenv()

from langsmith import Client
from langsmith.evaluation import evaluate
from agent.graph import run_agent

client = Client()

EVAL_DATASET = [
    # Product search (5)
    {"input": "Do you have running shoes?",                         "expected_tool": "search_products"},
    {"input": "Show me gym accessories under ₹1000",                "expected_tool": "search_products"},
    {"input": "What yoga equipment do you have?",                   "expected_tool": "search_products"},
    {"input": "I need something for muscle recovery after workout", "expected_tool": "search_products"},
    {"input": "Best rated products in your store",                  "expected_tool": "search_products"},
    # Order status (5)
    {"input": "Where is my order ORD-1001?",                        "expected_tool": "check_order"},
    {"input": "Track my order ORD-1002",                            "expected_tool": "check_order"},
    {"input": "Has ORD-1003 been shipped yet?",                     "expected_tool": "check_order"},
    {"input": "What is the status of ORD-1004?",                    "expected_tool": "check_order"},
    {"input": "What is the tracking ID for ORD-1001?",              "expected_tool": "check_order"},
    # Policy (5)
    {"input": "What is your return policy?",                        "expected_tool": "get_policy"},
    {"input": "How do I return a product?",                         "expected_tool": "get_policy"},
    {"input": "How long does shipping take?",                       "expected_tool": "get_policy"},
    {"input": "Do you offer free shipping?",                        "expected_tool": "get_policy"},
    {"input": "Can I return a yoga mat?",                           "expected_tool": "get_policy"},
    # Bundle (3)
    {"input": "I'm buying running shoes, what else should I get?",  "expected_tool": "recommend_bundle"},
    {"input": "Suggest something to go with the yoga mat",          "expected_tool": "recommend_bundle"},
    {"input": "What products go well with a hiking backpack?",      "expected_tool": "recommend_bundle"},
    # Escalation — agent should answer without calling any tool (2)
    {"input": "I want to speak to a human",                         "expected_tool": None},
    {"input": "My account was hacked, help!",                       "expected_tool": None},
]


def target_function(inputs: dict) -> dict:
    """Wrapper that LangSmith calls for each test case."""
    time.sleep(3)  # avoid Groq free tier rate limit (6000 TPM)
    try:
        result = run_agent(inputs["input"])
        return {
            "answer": result["answer"],
            "tools_used": result["tool_calls_made"],
            "escalate": result["escalate"],
        }
    except Exception as e:
        return {"answer": f"ERROR: {str(e)}", "tools_used": [], "escalate": False}


def tool_routing_evaluator(run, example) -> dict:
    """
    Checks if the correct tool was called.
    Score 1.0 = correct, 0.0 = wrong.
    """
    expected = example.outputs.get("expected_tool")
    tools_used = run.outputs.get("tools_used", [])

    if expected is None:
        # Escalation cases — no tool should be called
        score = 1.0 if len(tools_used) == 0 else 0.0
    else:
        score = 1.0 if expected in tools_used else 0.0

    return {"key": "tool_routing_accuracy", "score": score}


def run_evals():
    dataset_name = "ShopMind-Eval-v1"

    # Create dataset (skip if already exists)
    try:
        dataset = client.create_dataset(dataset_name)
        for item in EVAL_DATASET:
            client.create_example(
                inputs={"input": item["input"]},
                outputs={"expected_tool": item["expected_tool"]},
                dataset_id=dataset.id,
            )
        print(f"Created dataset: {dataset_name} with {len(EVAL_DATASET)} examples")
    except Exception:
        print(f"Dataset '{dataset_name}' already exists, reusing.")

    # Run evaluation
    results = evaluate(
        target_function,
        data=dataset_name,
        evaluators=[tool_routing_evaluator],
        experiment_prefix="shopmind-baseline",
        max_concurrency=1,      # run one at a time to avoid rate limits
    )

    print("\n── Eval Results ──────────────────────────────")
    scores = []
    for r in results:
        try:
            score = r["evaluation_results"]["results"][0].score
            scores.append(score)
        except Exception:
            pass

    if scores:
        print(f"Tool routing accuracy: {sum(scores)/len(scores)*100:.1f}%")
        print(f"Passed: {sum(1 for s in scores if s == 1.0)}/{len(scores)}")
    print("\nView full traces at: https://smith.langchain.com")


if __name__ == "__main__":
    run_evals()