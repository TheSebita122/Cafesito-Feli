from pathlib import Path

import pandas as pd
import pytest

from cafesito import cli
from cafesito.config import Settings
from cafesito.ml.artifacts import DEMAND_FILE


@pytest.fixture
def isolated_settings(tmp_path: Path, sales_frame: pd.DataFrame) -> Settings:
    csv_path = tmp_path / "sales.csv"
    sales_frame.to_csv(csv_path, index=False)
    return Settings(
        database_path=tmp_path / "cli.db",
        sales_csv_path=csv_path,
        models_dir=tmp_path / "models",
    )


def test_bootstrap_seeds_database_and_trains_models(
    isolated_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "get_settings", lambda: isolated_settings)
    assert cli.main(["bootstrap"]) == 0
    assert isolated_settings.database_path.exists()
    assert (isolated_settings.models_dir / DEMAND_FILE).exists()


def test_bootstrap_skips_work_when_everything_exists(
    isolated_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "get_settings", lambda: isolated_settings)
    cli.main(["bootstrap"])
    modified = (isolated_settings.models_dir / DEMAND_FILE).stat().st_mtime_ns
    cli.main(["bootstrap"])
    assert (isolated_settings.models_dir / DEMAND_FILE).stat().st_mtime_ns == modified


def test_seed_reports_missing_csv_with_nonzero_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = Settings(database_path=tmp_path / "x.db", sales_csv_path=tmp_path / "none.csv")
    monkeypatch.setattr(cli, "get_settings", lambda: settings)
    assert cli.main(["seed"]) == 1


def test_unknown_command_is_rejected() -> None:
    with pytest.raises(SystemExit):
        cli.main(["explode"])
