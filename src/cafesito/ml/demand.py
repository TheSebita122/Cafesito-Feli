from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier

NUMERIC_FEATURES = ["hour", "weekday", "month"]
STORE_FEATURE = "store_id"
FEATURES = [*NUMERIC_FEATURES, STORE_FEATURE]
DEFAULT_DEPTHS: tuple[int | None, ...] = (1, 3, 5, 8, 12, None)


@dataclass(frozen=True)
class DemandPrediction:
    is_high: bool
    probability_high: float


@dataclass
class DemandModel:
    pipeline: Pipeline
    threshold: float
    max_depth: int | None
    store_ids: list[int]
    hours: list[int]
    months: list[int]
    feature_importances: dict[str, float] = field(default_factory=dict)

    def predict(self, hour: int, weekday: int, month: int, store_id: int) -> DemandPrediction:
        row = pd.DataFrame(
            [{"hour": hour, "weekday": weekday, "month": month, "store_id": store_id}]
        )
        probabilities = self.pipeline.predict_proba(row)[0]
        classes = list(self.pipeline.classes_)
        probability_high = float(probabilities[classes.index(1)]) if 1 in classes else 0.0
        return DemandPrediction(is_high=probability_high >= 0.5, probability_high=probability_high)


def label_blocks(blocks: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    threshold = float(blocks["transactions"].median())
    labelled = blocks.copy()
    labelled["high_demand"] = (labelled["transactions"] > threshold).astype(int)
    return labelled, threshold


def build_pipeline(store_ids: list[int], max_depth: int | None, seed: int) -> Pipeline:
    encoder = ColumnTransformer(
        [
            (
                "store",
                OneHotEncoder(categories=[sorted(store_ids)], handle_unknown="error"),
                [STORE_FEATURE],
            ),
            ("numeric", "passthrough", NUMERIC_FEATURES),
        ]
    )
    tree = DecisionTreeClassifier(max_depth=max_depth, random_state=seed)
    return Pipeline([("encode", encoder), ("tree", tree)])


def aggregate_importances(pipeline: Pipeline) -> dict[str, float]:
    names = pipeline.named_steps["encode"].get_feature_names_out()
    importances = pipeline.named_steps["tree"].feature_importances_
    totals: dict[str, float] = {}
    for name, value in zip(names, importances, strict=True):
        key = "store" if name.startswith("store__") else name.removeprefix("numeric__")
        totals[key] = totals.get(key, 0.0) + float(value)
    return dict(sorted(totals.items(), key=lambda item: item[1], reverse=True))


def train_demand_model(
    blocks: pd.DataFrame,
    depths: tuple[int | None, ...] = DEFAULT_DEPTHS,
    test_size: float = 0.3,
    seed: int = 42,
) -> tuple[DemandModel, dict[str, Any]]:
    labelled, threshold = label_blocks(blocks)
    features = labelled[FEATURES]
    target = labelled["high_demand"]
    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=test_size, stratify=target, random_state=seed
    )
    store_ids = sorted(int(value) for value in labelled[STORE_FEATURE].unique())

    sweep: list[dict[str, Any]] = []
    best_depth: int | None = None
    best_accuracy = -1.0
    for depth in depths:
        candidate = build_pipeline(store_ids, depth, seed).fit(x_train, y_train)
        train_accuracy = float(accuracy_score(y_train, candidate.predict(x_train)))
        test_accuracy = float(accuracy_score(y_test, candidate.predict(x_test)))
        sweep.append(
            {
                "max_depth": depth,
                "leaves": int(candidate.named_steps["tree"].get_n_leaves()),
                "train_accuracy": train_accuracy,
                "test_accuracy": test_accuracy,
            }
        )
        if test_accuracy > best_accuracy:
            best_accuracy = test_accuracy
            best_depth = depth

    pipeline = build_pipeline(store_ids, best_depth, seed).fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    matrix = confusion_matrix(y_test, predictions, labels=[0, 1])
    true_negative, false_positive, false_negative, true_positive = (int(v) for v in matrix.ravel())
    baseline = float(max(y_test.mean(), 1 - y_test.mean()))
    recall = true_positive / max(true_positive + false_negative, 1)
    precision = true_positive / max(true_positive + false_positive, 1)

    model = DemandModel(
        pipeline=pipeline,
        threshold=threshold,
        max_depth=best_depth,
        store_ids=store_ids,
        hours=sorted(int(v) for v in labelled["hour"].unique()),
        months=sorted(int(v) for v in labelled["month"].unique()),
        feature_importances=aggregate_importances(pipeline),
    )
    report = {
        "blocks": len(labelled),
        "train_size": len(x_train),
        "test_size": len(x_test),
        "threshold": threshold,
        "high_demand_share": float(np.mean(target)),
        "chosen_max_depth": best_depth,
        "accuracy": float(accuracy_score(y_test, predictions)),
        "baseline_accuracy": baseline,
        "recall_high": recall,
        "precision_high": precision,
        "confusion_matrix": {
            "true_negative": true_negative,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "true_positive": true_positive,
        },
        "depth_sweep": sweep,
        "feature_importances": model.feature_importances,
    }
    return model, report
