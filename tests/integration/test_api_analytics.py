import pandas as pd
import pytest
from fastapi.testclient import TestClient


def test_health_reports_ready_services(client: TestClient) -> None:
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["database_ready"] is True
    assert body["demand_model_ready"] is True
    assert body["segmentation_ready"] is True
    assert body["rules_ready"] is True


def test_health_degrades_without_models(untrained_client: TestClient) -> None:
    body = untrained_client.get("/api/health").json()
    assert body["demand_model_ready"] is False
    assert body["rules_ready"] is False


def test_stores_lists_all_locations(client: TestClient) -> None:
    body = client.get("/api/stores").json()
    assert {store["location"] for store in body} == {"Alpha Street", "Beta Avenue", "Gamma Square"}


def test_kpis_match_dataset(client: TestClient, sales_frame: pd.DataFrame) -> None:
    body = client.get("/api/kpis").json()
    assert body["transactions"] == len(sales_frame)
    assert body["units"] == sales_frame["transaction_qty"].sum()
    assert body["variation"] is None
    assert body["average_ticket"] == pytest.approx(body["revenue"] / body["transactions"])


def test_kpis_include_variation_against_previous_quarter(client: TestClient) -> None:
    body = client.get("/api/kpis", params={"quarter": 2}).json()
    assert body["variation"] is None or set(body["variation"]) == {
        "revenue",
        "transactions",
        "units",
        "average_ticket",
    }


def test_kpis_store_filter(client: TestClient) -> None:
    everyone = client.get("/api/kpis").json()
    one = client.get("/api/kpis", params={"store_id": 1}).json()
    assert one["transactions"] < everyone["transactions"]


def test_kpis_reject_invalid_quarter(client: TestClient) -> None:
    response = client.get("/api/kpis", params={"quarter": 7})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"
    assert "trimestre" in response.json()["error"]["message"]


def test_sales_by_category(client: TestClient) -> None:
    body = client.get("/api/sales/by-category").json()
    revenues = [row["revenue"] for row in body]
    assert revenues == sorted(revenues, reverse=True)


def test_sales_monthly(client: TestClient) -> None:
    body = client.get("/api/sales/monthly").json()
    assert [row["month"] for row in body] == [1, 2]


def test_sales_hourly(client: TestClient) -> None:
    body = client.get("/api/sales/hourly").json()
    assert body[0]["hour"] == 7


def test_top_products_default_and_limit(client: TestClient) -> None:
    assert len(client.get("/api/products/top").json()) == 5
    assert len(client.get("/api/products/top", params={"limit": 2}).json()) == 2


def test_top_products_reject_invalid_limit(client: TestClient) -> None:
    assert client.get("/api/products/top", params={"limit": 0}).status_code == 422
    assert client.get("/api/products/top", params={"limit": 500}).status_code == 422
