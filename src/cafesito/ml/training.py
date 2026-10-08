import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import Engine

from cafesito.ml import dataset
from cafesito.ml.artifacts import save_artifacts
from cafesito.ml.association import mine_rules
from cafesito.ml.demand import DEFAULT_DEPTHS, train_demand_model
from cafesito.ml.segmentation import segment_products

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TrainingConfig:
    seed: int = 42
    test_size: float = 0.3
    depths: tuple[int | None, ...] = DEFAULT_DEPTHS
    clusters: int = 3
    min_support: float = 0.005
    min_lift: float = 1.0


def train_all(
    engine: Engine, models_dir: Path, config: TrainingConfig | None = None
) -> dict[str, Any]:
    config = config or TrainingConfig()

    logger.info("Training demand classifier")
    demand_model, demand_report = train_demand_model(
        dataset.load_demand_blocks(engine),
        depths=config.depths,
        test_size=config.test_size,
        seed=config.seed,
    )

    logger.info("Segmenting products")
    segmentation_model, assignments, segmentation_report = segment_products(
        dataset.load_product_metrics(engine), k=config.clusters, seed=config.seed
    )

    logger.info("Mining association rules")
    baskets = dataset.load_baskets(engine)
    rules = mine_rules(baskets, min_support=config.min_support, min_lift=config.min_lift)

    metrics: dict[str, Any] = {
        "demand": demand_report,
        "segmentation": segmentation_report,
        "association": {
            "baskets": len(baskets),
            "multi_item_baskets": int((baskets.sum(axis=1) > 1).sum()),
            "min_support": config.min_support,
            "rules": len(rules),
            "rules_above_1_2_lift": sum(1 for rule in rules if rule.lift > 1.2),
        },
    }
    save_artifacts(models_dir, demand_model, segmentation_model, assignments, rules, metrics)
    logger.info("Artifacts written to %s", models_dir)
    return metrics
