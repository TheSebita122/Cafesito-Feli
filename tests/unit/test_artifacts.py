from pathlib import Path

from cafesito.ml import artifacts
from cafesito.ml.artifacts import ModelStore, load_artifacts


def test_load_artifacts_returns_empty_store_for_missing_directory(tmp_path: Path) -> None:
    store = load_artifacts(tmp_path / "does-not-exist")
    assert store.demand is None
    assert store.segmentation is None
    assert store.rules == []
    assert store.metrics == {}


def test_trained_artifacts_round_trip(models_dir: Path) -> None:
    store = load_artifacts(models_dir)
    assert store.demand is not None
    assert store.segmentation is not None
    assert store.rules
    assert len(store.segment_products) == 12
    assert store.metrics["demand"]["accuracy"] > 0


def test_loaded_model_can_predict(models_dir: Path) -> None:
    store = load_artifacts(models_dir)
    assert store.demand is not None
    assert 0.0 <= store.demand.predict(8, 1, 1, 1).probability_high <= 1.0


def test_corrupt_artifacts_fall_back_to_empty_store(tmp_path: Path) -> None:
    (tmp_path / artifacts.DEMAND_FILE).write_bytes(b"not a pickle")
    store = load_artifacts(tmp_path)
    assert store == ModelStore()


def test_corrupt_json_falls_back_to_empty_store(tmp_path: Path) -> None:
    (tmp_path / artifacts.RULES_FILE).write_text("{broken", encoding="utf-8")
    assert load_artifacts(tmp_path) == ModelStore()
