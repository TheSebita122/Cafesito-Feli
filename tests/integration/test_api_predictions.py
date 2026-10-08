import pytest
from fastapi.testclient import TestClient

VALID_PAYLOAD = {"hour": 8, "weekday": 2, "month": 1, "store_id": 1}


def test_demand_options_expose_valid_choices(client: TestClient) -> None:
    body = client.get("/api/predictions/demand/options").json()
    assert {store["id"] for store in body["stores"]} == {1, 2, 3}
    assert body["hours"][0] == 7
    assert body["months"] == [1, 2]
    assert 0 < body["accuracy"] <= 1


def test_predict_demand_returns_level_and_probability(client: TestClient) -> None:
    response = client.post("/api/predictions/demand", json=VALID_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["level"] in {"high", "low"}
    assert 0 <= body["probability_high"] <= 1
    assert body["store_location"] == "Alpha Street"


def test_morning_is_high_and_afternoon_is_low(client: TestClient) -> None:
    morning = client.post("/api/predictions/demand", json=VALID_PAYLOAD).json()
    afternoon = client.post("/api/predictions/demand", json={**VALID_PAYLOAD, "hour": 15}).json()
    assert morning["level"] == "high"
    assert afternoon["probability_high"] < morning["probability_high"]


@pytest.mark.parametrize(
    ("override", "fragment"),
    [
        ({"store_id": 999}, "sede"),
        ({"hour": 3}, "hora"),
        ({"month": 11}, "meses"),
    ],
)
def test_predict_demand_rejects_values_outside_training_range(
    client: TestClient, override: dict[str, int], fragment: str
) -> None:
    response = client.post("/api/predictions/demand", json={**VALID_PAYLOAD, **override})
    assert response.status_code == 422
    assert fragment in response.json()["error"]["message"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"hour": "abc", "weekday": 1, "month": 1, "store_id": 1},
        {"hour": 30, "weekday": 1, "month": 1, "store_id": 1},
        {"hour": 8, "weekday": 9, "month": 1, "store_id": 1},
        {"hour": 8, "weekday": 1, "month": 0, "store_id": 1},
    ],
)
def test_predict_demand_rejects_malformed_payloads_with_friendly_message(
    client: TestClient, payload: dict[str, object]
) -> None:
    response = client.post("/api/predictions/demand", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "invalid_input"
    assert "Traceback" not in response.text
    assert "pydantic" not in response.text.lower()


def test_predictions_return_503_when_model_is_missing(untrained_client: TestClient) -> None:
    response = untrained_client.post("/api/predictions/demand", json=VALID_PAYLOAD)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_unavailable"
    assert untrained_client.get("/api/predictions/demand/options").status_code == 503
