from fastapi.testclient import TestClient


def test_product_types_are_listed(client: TestClient) -> None:
    body = client.get("/api/product-types").json()
    assert "Scone" in body["product_types"]
    assert body["product_types"] == sorted(body["product_types"])


def test_recommendations_without_filter_return_all_rules(client: TestClient) -> None:
    body = client.get("/api/recommendations").json()
    assert body["product_type"] is None
    assert body["rules"]
    lifts = [rule["lift"] for rule in body["rules"]]
    assert lifts == sorted(lifts, reverse=True)


def test_recommendations_filter_by_antecedent(client: TestClient) -> None:
    body = client.get("/api/recommendations", params={"product_type": "Regular syrup"}).json()
    assert body["rules"]
    assert all("Regular syrup" in rule["antecedent"] for rule in body["rules"])


def test_recommendations_for_product_without_rules_are_empty(client: TestClient) -> None:
    response = client.get("/api/recommendations", params={"product_type": "Clothing"})
    assert response.status_code == 200
    assert response.json()["rules"] == []


def test_recommendations_reject_unknown_product_type(client: TestClient) -> None:
    response = client.get("/api/recommendations", params={"product_type": "Nonexistent"})
    assert response.status_code == 422
    assert "no existe" in response.json()["error"]["message"]


def test_recommendations_return_503_without_rules(untrained_client: TestClient) -> None:
    assert untrained_client.get("/api/recommendations").status_code == 503
