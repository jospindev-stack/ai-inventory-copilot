from math import ceil

from app.models import InventoryItem, RiskAssessment, RiskLevel


def assess_risk(item: InventoryItem) -> RiskAssessment:
    days_of_cover = item.on_hand / item.daily_demand
    reorder_point = item.daily_demand * item.lead_time_days + item.safety_stock
    demand_during_lead_time = item.daily_demand * item.lead_time_days
    projected_shortage = max(0.0, demand_during_lead_time + item.safety_stock - item.on_hand)

    coverage_ratio = days_of_cover / item.lead_time_days
    coverage_risk = max(0.0, min(1.0, 1.25 - coverage_ratio))
    reliability_risk = 1.0 - item.supplier_reliability
    stock_position_risk = max(0.0, min(1.0, (reorder_point - item.on_hand) / max(reorder_point, 1)))

    score = round(
        min(100.0, (coverage_risk * 55) + (stock_position_risk * 30) + (reliability_risk * 15)),
        1,
    )

    if score >= 75:
        level = RiskLevel.CRITICAL
    elif score >= 55:
        level = RiskLevel.HIGH
    elif score >= 30:
        level = RiskLevel.MEDIUM
    else:
        level = RiskLevel.LOW

    target_stock = item.daily_demand * (item.lead_time_days * 1.5) + item.safety_stock
    recommended_order_qty = max(0, ceil(target_stock - item.on_hand))

    reasons: list[str] = []
    if days_of_cover < item.lead_time_days:
        reasons.append("Stock coverage is shorter than supplier lead time.")
    if item.on_hand < reorder_point:
        reasons.append("Current stock is below the calculated reorder point.")
    if item.supplier_reliability < 0.9:
        reasons.append("Supplier reliability increases replenishment uncertainty.")
    if not reasons:
        reasons.append("Current stock position is within the expected operating range.")

    return RiskAssessment(
        sku=item.sku,
        risk_score=score,
        risk_level=level,
        days_of_cover=round(days_of_cover, 1),
        reorder_point=round(reorder_point, 1),
        projected_shortage=round(projected_shortage, 1),
        recommended_order_qty=recommended_order_qty,
        reasons=reasons,
    )
