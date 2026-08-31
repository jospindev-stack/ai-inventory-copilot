from app.models import InventoryItem, RiskLevel
from app.services.risk_engine import assess_risk


def make_item(**overrides):
    data = {
        "sku": "TEST-001",
        "name": "Test Item",
        "category": "Test",
        "on_hand": 300,
        "daily_demand": 10.0,
        "lead_time_days": 10,
        "supplier_reliability": 0.95,
        "safety_stock": 50,
        "unit_cost": 10.0,
        "supplier": "Test Supplier",
    }
    data.update(overrides)
    return InventoryItem(**data)


def test_low_risk_when_stock_is_healthy():
    result = assess_risk(make_item())
    assert result.risk_level == RiskLevel.LOW
    assert result.recommended_order_qty == 0


def test_critical_risk_when_stock_is_below_lead_time_demand():
    result = assess_risk(make_item(on_hand=20, supplier_reliability=0.8))
    assert result.risk_level == RiskLevel.CRITICAL
    assert result.projected_shortage > 0
    assert result.recommended_order_qty > 0


def test_reorder_point_includes_safety_stock():
    result = assess_risk(make_item(daily_demand=8, lead_time_days=12, safety_stock=40))
    assert result.reorder_point == 136.0


def test_days_of_cover_is_calculated_from_demand():
    result = assess_risk(make_item(on_hand=125, daily_demand=5))
    assert result.days_of_cover == 25.0


def test_score_stays_between_zero_and_one_hundred():
    low = assess_risk(make_item(on_hand=5000, supplier_reliability=1.0))
    high = assess_risk(make_item(on_hand=0, supplier_reliability=0.0))
    assert 0 <= low.risk_score <= 100
    assert 0 <= high.risk_score <= 100
