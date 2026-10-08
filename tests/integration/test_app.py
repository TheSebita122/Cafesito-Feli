from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cafesito.api.app import create_app
from cafesito.config import Settings


def test_unknown_api_route_returns_friendly_json(client: TestClient) -> None:
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "http_error"


def test_openapi_schema_is_published(client: TestClient) -> None:
    schema = client.get("/api/openapi.json").json()
    assert "/api/predictions/demand" in schema["paths"]


def test_frontend_index_is_served(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Cafesito Feli" in response.text


def test_frontend_assets_are_served(client: TestClient) -> None:
    assert client.get("/js/main.js").status_code == 200
    assert client.get("/css/style.css").status_code == 200


@pytest.fixture
def failing_client(database_path: Path, models_dir: Path) -> Iterator[TestClient]:
    app: FastAPI = create_app(Settings(database_path=database_path, models_dir=models_dir))

    def boom() -> None:
        raise RuntimeError("secret internal detail")

    app.add_api_route("/api/boom", boom, methods=["GET"])
    app.router.routes.insert(0, app.router.routes.pop())

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_unexpected_errors_never_leak_internal_details(failing_client: TestClient) -> None:
    response = failing_client.get("/api/boom")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "secret internal detail" not in response.text
    assert "Traceback" not in response.text
