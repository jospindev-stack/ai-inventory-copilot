from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_products_endpoint_returns_inventory():
    response = client.get("/products")
    assert response.status_code == 200
    assert len(response.json()) == 40


def test_dashboard_endpoint_returns_summary():
    response = client.get("/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 40
    assert body["inventory_value"] > 0


def test_unknown_sku_returns_404():
    response = client.get("/products/UNKNOWN/risk")
    assert response.status_code == 404


def test_export_endpoint_returns_excel_file():
    response = client.get("/export")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
