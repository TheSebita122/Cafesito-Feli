from pathlib import Path

import pytest
from pydantic import ValidationError

from cafesito.config import Settings


def test_database_url_uses_posix_path() -> None:
    settings = Settings(database_path=Path("data") / "x.db")
    assert settings.database_url == "sqlite:///data/x.db"


def test_environment_variables_override_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAFESITO_PORT", "9100")
    monkeypatch.setenv("CAFESITO_HOST", "0.0.0.0")
    settings = Settings()
    assert settings.port == 9100
    assert settings.host == "0.0.0.0"


def test_invalid_port_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(port=70000)
