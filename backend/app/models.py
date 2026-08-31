from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InventoryItem(BaseModel):
    sku: str
    name: str
    category: str
    on_hand: int = Field(ge=0)
    daily_demand: float = Field(gt=0)
    lead_time_days: int = Field(gt=0)
    supplier_reliability: float = Field(ge=0, le=1)
    safety_stock: int = Field(ge=0)
    unit_cost: float = Field(gt=0)
    supplier: str


class RiskAssessment(BaseModel):
    sku: str
    risk_score: float = Field(ge=0, le=100)
    risk_level: RiskLevel
    days_of_cover: float
    reorder_point: float
    projected_shortage: float
    recommended_order_qty: int
    reasons: list[str]


class DashboardSummary(BaseModel):
    total_items: int
    inventory_value: float
    critical_items: int
    high_risk_items: int
    medium_risk_items: int
    low_risk_items: int
    average_risk_score: float


class CopilotRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    sku: str | None = None


class CopilotResponse(BaseModel):
    answer: str
    source: Literal["ollama", "fallback"]
