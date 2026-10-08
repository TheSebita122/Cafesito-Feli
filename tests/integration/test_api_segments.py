from fastapi.testclient import TestClient


def test_segments_return_profiles_and_products(client: TestClient) -> None:
    body = client.get("/api/segments").json()
    assert len(body["products"]) == 12
    assert {profile["segment"] for profile in body["profiles"]} == {
        "star",
        "complement",
        "premium_niche",
    }
    assert -1 <= body["silhouette"] <= 1


def test_classify_returns_segment(client: TestClient) -> None:
    response = client.post(
        "/api/segments/classify", json={"units": 100, "revenue": 2500, "avg_price": 22}
    )
    assert response.status_code == 200
    assert response.json()["segment"] == "premium_niche"


def test_classify_rejects_invalid_numbers(client: TestClient) -> None:
    response = client.post(
        "/api/segments/classify", json={"units": -5, "revenue": 100, "avg_price": 0}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"


def test_segments_return_503_without_models(untrained_client: TestClient) -> None:
    assert untrained_client.get("/api/segments").status_code == 503
    payload = {"units": 1, "revenue": 1, "avg_price": 1}
    assert untrained_client.post("/api/segments/classify", json=payload).status_code == 503
