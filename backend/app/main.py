from io import BytesIO

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openpyxl import Workbook

from app.models import CopilotRequest, CopilotResponse, DashboardSummary, InventoryItem, RiskAssessment
from app.services.copilot import ask_copilot
from app.services.data_generator import generate_inventory
from app.services.risk_engine import assess_risk

app = FastAPI(title="AI Inventory Copilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

inventory = generate_inventory()


def _find_item(sku: str) -> InventoryItem:
    item = next((item for item in inventory if item.sku == sku), None)
    if item is None:
        raise HTTPException(status_code=404, detail="SKU not found")
    return item


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/products", response_model=list[InventoryItem])
def list_products(
    risk: str | None = Query(default=None),
    search: str | None = Query(default=None),
) -> list[InventoryItem]:
    items = inventory

    if search:
        term = search.lower().strip()
        items = [item for item in items if term in item.sku.lower() or term in item.name.lower()]

    if risk:
        items = [item for item in items if assess_risk(item).risk_level.value == risk.lower()]

    return items


@app.get("/products/{sku}/risk", response_model=RiskAssessment)
def product_risk(sku: str) -> RiskAssessment:
    return assess_risk(_find_item(sku))


@app.get("/risks", response_model=list[RiskAssessment])
def list_risks() -> list[RiskAssessment]:
    return sorted(
        (assess_risk(item) for item in inventory),
        key=lambda result: result.risk_score,
        reverse=True,
    )


@app.get("/dashboard", response_model=DashboardSummary)
def dashboard() -> DashboardSummary:
    assessments = [assess_risk(item) for item in inventory]
    counts = {level: sum(1 for result in assessments if result.risk_level.value == level) for level in ["critical", "high", "medium", "low"]}

    return DashboardSummary(
        total_items=len(inventory),
        inventory_value=round(sum(item.on_hand * item.unit_cost for item in inventory), 2),
        critical_items=counts["critical"],
        high_risk_items=counts["high"],
        medium_risk_items=counts["medium"],
        low_risk_items=counts["low"],
        average_risk_score=round(sum(result.risk_score for result in assessments) / len(assessments), 1),
    )


@app.post("/copilot", response_model=CopilotResponse)
async def copilot(request: CopilotRequest) -> CopilotResponse:
    item = _find_item(request.sku) if request.sku else None
    assessment = assess_risk(item) if item else None
    answer, source = await ask_copilot(request.question, item, assessment)
    return CopilotResponse(answer=answer, source=source)


@app.get("/export")
def export_inventory() -> StreamingResponse:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Inventory Risk"
    sheet.append([
        "SKU", "Name", "Category", "On Hand", "Daily Demand", "Lead Time",
        "Supplier", "Reliability", "Risk Score", "Risk Level", "Days of Cover",
        "Reorder Point", "Recommended Order Qty",
    ])

    for item in inventory:
        risk = assess_risk(item)
        sheet.append([
            item.sku, item.name, item.category, item.on_hand, item.daily_demand,
            item.lead_time_days, item.supplier, item.supplier_reliability,
            risk.risk_score, risk.risk_level.value, risk.days_of_cover,
            risk.reorder_point, risk.recommended_order_qty,
        ])

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=inventory-risk-report.xlsx"},
    )
