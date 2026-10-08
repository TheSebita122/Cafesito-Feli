from pathlib import Path

from sqlalchemy import Engine

from cafesito.ml import artifacts
from cafesito.ml.training import TrainingConfig, train_all


def test_train_all_writes_every_artifact(engine: Engine, tmp_path: Path) -> None:
    metrics = train_all(engine, tmp_path / "out", TrainingConfig(min_support=0.01, depths=(3,)))
    for name in (
        artifacts.DEMAND_FILE,
        artifacts.SEGMENTATION_FILE,
        artifacts.SEGMENT_PRODUCTS_FILE,
        artifacts.RULES_FILE,
        artifacts.METRICS_FILE,
    ):
        assert (tmp_path / "out" / name).exists()
    assert set(metrics) == {"demand", "segmentation", "association"}
    assert metrics["association"]["rules"] >= 1
    assert metrics["association"]["baskets"] > metrics["association"]["multi_item_baskets"] > 0
