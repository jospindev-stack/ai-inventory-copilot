import os

import httpx

from app.models import InventoryItem, RiskAssessment


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")


def _fallback_answer(item: InventoryItem | None, assessment: RiskAssessment | None) -> str:
    if item and assessment:
        reasons = " ".join(assessment.reasons)
        return (
            f"{item.sku} is currently classified as {assessment.risk_level.value} risk "
            f"with a score of {assessment.risk_score}/100. It has {assessment.days_of_cover} days "
            f"of stock coverage compared with a {item.lead_time_days}-day supplier lead time. "
            f"The recommended order quantity is {assessment.recommended_order_qty} units. {reasons}"
        )

    return (
        "The inventory copilot uses stock coverage, reorder position, supplier lead time and "
        "supplier reliability to prioritize replenishment risk. Select a SKU for a specific recommendation."
    )


async def ask_copilot(
    question: str,
    item: InventoryItem | None = None,
    assessment: RiskAssessment | None = None,
) -> tuple[str, str]:
    context = "No SKU selected."
    if item and assessment:
        context = (
            f"SKU={item.sku}; name={item.name}; on_hand={item.on_hand}; daily_demand={item.daily_demand}; "
            f"lead_time_days={item.lead_time_days}; supplier_reliability={item.supplier_reliability}; "
            f"safety_stock={item.safety_stock}; risk_score={assessment.risk_score}; "
            f"risk_level={assessment.risk_level.value}; days_of_cover={assessment.days_of_cover}; "
            f"recommended_order_qty={assessment.recommended_order_qty}; reasons={assessment.reasons}."
        )

    prompt = (
        "You are an inventory planning assistant for a manufacturing company. "
        "Use only the supplied inventory context. Be concise, practical and explain the operational reason. "
        "Do not invent missing facts.\n\n"
        f"Inventory context: {context}\n"
        f"Question: {question}"
    )

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            answer = response.json().get("response", "").strip()
            if answer:
                return answer, "ollama"
    except (httpx.HTTPError, ValueError):
        pass

    return _fallback_answer(item, assessment), "fallback"
