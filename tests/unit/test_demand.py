from typing import Any

import pandas as pd
import pytest
from sqlalchemy import Engine

from cafesito.ml.dataset import load_demand_blocks
from cafesito.ml.demand import DemandModel, label_blocks, train_demand_model


@pytest.fixture(scope="module")
def blocks(engine: Engine) -> pd.DataFrame:
    return load_demand_blocks(engine)


@pytest.fixture(scope="module")
def trained(blocks: pd.DataFrame) -> tuple[DemandModel, dict[str, Any]]:
    return train_demand_model(blocks, depths=(2, 4, None))


def test_label_blocks_uses_median_threshold() -> None:
    blocks = pd.DataFrame({"transactions": [1, 2, 3, 4, 5]})
    labelled, threshold = label_blocks(blocks)
    assert threshold == 3
    assert labelled["high_demand"].tolist() == [0, 0, 0, 1, 1]


def test_blocks_aggregate_sales_by_store_date_and_hour(blocks: pd.DataFrame) -> None:
    assert {"store_id", "hour", "weekday", "month", "transactions"} <= set(blocks.columns)
    assert blocks["transactions"].min() >= 1


def test_training_report_is_consistent(trained: tuple[DemandModel, dict[str, Any]]) -> None:
    _, report = trained
    matrix = report["confusion_matrix"]
    assert isinstance(matrix, dict)
    assert sum(matrix.values()) == report["test_size"]
    assert 0.0 <= report["accuracy"] <= 1.0


def test_model_beats_majority_baseline(trained: tuple[DemandModel, dict[str, Any]]) -> None:
    _, report = trained
    assert report["accuracy"] > report["baseline_accuracy"]


def test_depth_sweep_reports_every_candidate(trained: tuple[DemandModel, dict[str, Any]]) -> None:
    _, report = trained
    sweep = report["depth_sweep"]
    assert isinstance(sweep, list)
    assert [row["max_depth"] for row in sweep] == [2, 4, None]


def test_training_is_deterministic(blocks: pd.DataFrame) -> None:
    _, first = train_demand_model(blocks, depths=(3,))
    _, second = train_demand_model(blocks, depths=(3,))
    assert first["accuracy"] == second["accuracy"]


def test_morning_rush_predicts_higher_probability_than_afternoon(
    trained: tuple[DemandModel, dict[str, Any]],
) -> None:
    model, _ = trained
    morning = model.predict(hour=8, weekday=2, month=2, store_id=1)
    afternoon = model.predict(hour=15, weekday=2, month=2, store_id=1)
    assert morning.probability_high > afternoon.probability_high
    assert morning.is_high is True


def test_prediction_probability_is_bounded(trained: tuple[DemandModel, dict[str, Any]]) -> None:
    model, _ = trained
    prediction = model.predict(hour=10, weekday=0, month=1, store_id=2)
    assert 0.0 <= prediction.probability_high <= 1.0


def test_feature_importances_sum_to_one(trained: tuple[DemandModel, dict[str, Any]]) -> None:
    model, _ = trained
    assert sum(model.feature_importances.values()) == pytest.approx(1.0)
    assert set(model.feature_importances) == {"hour", "weekday", "month", "store"}


def test_unknown_store_is_rejected_by_encoder(
    trained: tuple[DemandModel, dict[str, Any]],
) -> None:
    model, _ = trained
    with pytest.raises(ValueError, match="Found unknown categories"):
        model.predict(hour=8, weekday=1, month=1, store_id=999)
