import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from cafesito.ml.association import Rule
from cafesito.ml.demand import DemandModel
from cafesito.ml.segmentation import SegmentationModel

logger = logging.getLogger(__name__)

DEMAND_FILE = "demand_tree.joblib"
SEGMENTATION_FILE = "segmentation.joblib"
SEGMENT_PRODUCTS_FILE = "segment_products.json"
RULES_FILE = "association_rules.json"
METRICS_FILE = "metrics.json"


@dataclass
class ModelStore:
    demand: DemandModel | None = None
    segmentation: SegmentationModel | None = None
    segment_products: list[dict[str, Any]] = field(default_factory=list)
    rules: list[Rule] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


def save_artifacts(
    models_dir: Path,
    demand: DemandModel,
    segmentation: SegmentationModel,
    segment_products: pd.DataFrame,
    rules: list[Rule],
    metrics: dict[str, Any],
) -> None:
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(demand, models_dir / DEMAND_FILE)
    joblib.dump(segmentation, models_dir / SEGMENTATION_FILE)
    products = segment_products[
        [
            "product_id",
            "detail",
            "category",
            "product_type",
            "units",
            "revenue",
            "avg_price",
            "segment",
        ]
    ]
    write_json(models_dir / SEGMENT_PRODUCTS_FILE, products.to_dict("records"))
    write_json(models_dir / RULES_FILE, [rule.model_dump() for rule in rules])
    write_json(models_dir / METRICS_FILE, metrics)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")


def _json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"Cannot serialise {type(value)!r}")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_artifacts(models_dir: Path) -> ModelStore:
    store = ModelStore()
    try:
        if (models_dir / DEMAND_FILE).exists():
            store.demand = joblib.load(models_dir / DEMAND_FILE)
        if (models_dir / SEGMENTATION_FILE).exists():
            store.segmentation = joblib.load(models_dir / SEGMENTATION_FILE)
        if (models_dir / SEGMENT_PRODUCTS_FILE).exists():
            store.segment_products = read_json(models_dir / SEGMENT_PRODUCTS_FILE)
        if (models_dir / RULES_FILE).exists():
            store.rules = [Rule.model_validate(item) for item in read_json(models_dir / RULES_FILE)]
        if (models_dir / METRICS_FILE).exists():
            store.metrics = read_json(models_dir / METRICS_FILE)
    except Exception:
        logger.exception("Could not load model artifacts from %s", models_dir)
        return ModelStore()
    return store
