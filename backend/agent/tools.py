"""
tools.py — LangChain @tool functions
Each tool is a pure Python function decorated with @tool.
The LLM decides which tool to call based on the user query.
LangGraph's ToolNode executes them automatically.
"""

import json
import os
from pathlib import Path
from langchain_core.tools import tool

DATA_DIR = Path(__file__).parent.parent / "data"


# ── 1. PRODUCT SEARCH (semantic via FAISS) ────────────────────────────────────
# On first call we build the FAISS index from products.json.
# In production you'd persist this index to disk.

_product_index = None
_products = None

def _build_product_index():
    """Lazy-load products and build FAISS index with sentence-transformers."""
    global _product_index, _products

    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np

    with open(DATA_DIR / "products.json") as f:
        _products = json.load(f)

    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Combine name + description + tags into one text blob per product
    texts = [
        f"{p['name']}. {p['description']}. Tags: {', '.join(p['tags'])}"
        for p in _products
    ]
    embeddings = model.encode(texts, convert_to_numpy=True).astype("float32")

    dimension = embeddings.shape[1]
    _product_index = faiss.IndexFlatL2(dimension)
    _product_index.add(embeddings)

    return model


_embed_model = None

@tool
def search_products(query: str, top_k: int = 3) -> str:
    """
    Search the product catalog using semantic similarity.
    Use this when the customer asks about products, what's available,
    product details, price, or stock.
    """
    global _product_index, _products, _embed_model
    import numpy as np

    if _product_index is None:
        _embed_model = _build_product_index()

    q_vec = _embed_model.encode([query], convert_to_numpy=True).astype("float32")
    distances, indices = _product_index.search(q_vec, top_k)

    results = []
    for idx in indices[0]:
        p = _products[idx]
        results.append({
            "id": p["id"],
            "name": p["name"],
            "price": f"₹{p['price']}",
            "rating": p["rating"],
            "stock": p["stock"],
            "description": p["description"][:120] + "..."
        })

    return json.dumps(results, indent=2)


# ── 2. ORDER STATUS (deterministic — no LLM guessing) ─────────────────────────
@tool
def check_order(order_id: str) -> str:
    """
    Look up the status of a customer order by order ID.
    Use this when the customer asks about their order, delivery, tracking, or shipment.
    Order IDs follow the format ORD-XXXX (e.g. ORD-1001).
    Always use this tool for order questions — never guess the status.
    """
    with open(DATA_DIR / "orders.json") as f:
        orders = json.load(f)

    order_id = order_id.strip().upper()
    order = orders.get(order_id)

    if not order:
        return json.dumps({
            "found": False,
            "message": f"No order found with ID {order_id}. Please check the order ID and try again."
        })

    status_messages = {
        "processing":        "Your order is being prepared and will be shipped soon.",
        "out_for_delivery":  "Your order is out for delivery today!",
        "delivered":         f"Your order was delivered on {order['delivered_on']}.",
        "cancelled":         "Your order has been cancelled."
    }

    return json.dumps({
        "found": True,
        "order_id": order["order_id"],
        "status": order["status"],
        "status_message": status_messages.get(order["status"], "Status unknown."),
        "items": order["items"],
        "total": f"₹{order['total']}",
        "placed_on": order["placed_on"],
        "tracking_id": order["tracking_id"] or "Not yet assigned",
        "address": order["address"]
    }, indent=2)


# ── 3. POLICY RAG (retrieval over policy docs) ────────────────────────────────
_policy_cache = None

def _load_policies():
    global _policy_cache
    if _policy_cache is None:
        _policy_cache = {}
        policy_dir = DATA_DIR / "policies"
        for f in policy_dir.glob("*.txt"):
            _policy_cache[f.stem] = f.read_text()
    return _policy_cache

@tool
def get_policy(topic: str) -> str:
    """
    Retrieve store policy information on a given topic.
    Use this when the customer asks about returns, refunds, shipping,
    delivery times, or any store policy.
    Topic should be one of: 'returns', 'shipping'.
    """
    policies = _load_policies()
    topic = topic.lower().strip()

    # Simple keyword match — swap for FAISS in production
    if "return" in topic or "refund" in topic:
        return policies.get("returns", "Return policy not found.")
    elif "ship" in topic or "deliver" in topic:
        return policies.get("shipping", "Shipping policy not found.")
    else:
        # Return all policies if topic is unclear
        return "\n\n---\n\n".join(policies.values())


# ── 4. BUNDLE RECOMMENDER (upsell logic) ──────────────────────────────────────
BUNDLE_MAP = {
    "P001": ["P004", "P002", "P007"],   # Running shoes → sports tee, water bottle, shaker
    "P006": ["P002", "P003", "P005"],   # Yoga mat → water bottle, bands, foam roller
    "P008": ["P002", "P005", "P004"],   # Backpack → water bottle, foam roller, tee
    "P003": ["P005", "P004", "P007"],   # Bands → foam roller, tee, shaker
    "P005": ["P003", "P002", "P004"],   # Foam roller → bands, water bottle, tee
}

@tool
def recommend_bundle(product_id: str) -> str:
    """
    Suggest complementary products to bundle with a given product.
    Use this when the customer shows interest in a product and
    you want to suggest add-ons to increase order value.
    Pass the product ID (e.g. P001).
    """
    with open(DATA_DIR / "products.json") as f:
        products = json.load(f)

    product_map = {p["id"]: p for p in products}
    bundle_ids = BUNDLE_MAP.get(product_id.upper(), [])

    if not bundle_ids:
        return json.dumps({"message": "No bundle recommendations available for this product."})

    base_product = product_map.get(product_id.upper())
    bundles = [product_map[pid] for pid in bundle_ids if pid in product_map]

    total_savings = int(sum(b["price"] for b in bundles) * 0.10)  # 10% bundle discount

    return json.dumps({
        "base_product": base_product["name"] if base_product else product_id,
        "recommended_bundles": [
            {"id": b["id"], "name": b["name"], "price": f"₹{b['price']}", "rating": b["rating"]}
            for b in bundles
        ],
        "bundle_discount": "10% off when bought together",
        "estimated_savings": f"₹{total_savings}"
    }, indent=2)


# ── Export all tools as a list ─────────────────────────────────────────────────
ALL_TOOLS = [search_products, check_order, get_policy, recommend_bundle]