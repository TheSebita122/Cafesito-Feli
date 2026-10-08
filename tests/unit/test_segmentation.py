import pandas as pd
import pytest
from sqlalchemy import Engine

from cafesito.ml.dataset import load_product_metrics
from cafesito.ml.segmentation import (
    COMPLEMENT,
    PREMIUM_NICHE,
    STAR,
    name_clusters,
    segment_products,
)


@pytest.fixture(scope="module")
def metrics(engine: Engine) -> pd.DataFrame:
    return load_product_metrics(engine)


def test_name_clusters_assigns_business_names() -> None:
    centers = pd.DataFrame(
        {"units": [4000.0, 150.0, 2000.0], "avg_price": [3.0, 20.0, 2.5]}, index=[0, 1, 2]
    )
    assert name_clusters(centers) == {0: STAR, 1: PREMIUM_NICHE, 2: COMPLEMENT}


def test_name_clusters_falls_back_for_other_cluster_counts() -> None:
    centers = pd.DataFrame({"units": [1.0, 2.0], "avg_price": [1.0, 2.0]}, index=[0, 1])
    assert name_clusters(centers) == {0: "segment_0", 1: "segment_1"}


def test_product_metrics_cover_every_product(metrics: pd.DataFrame) -> None:
    assert len(metrics) == 12
    assert (metrics["units"] > 0).all()


def test_segmentation_assigns_every_product(metrics: pd.DataFrame) -> None:
    _, assigned, report = segment_products(metrics)
    assert assigned["segment"].notna().all()
    assert set(assigned["segment"]) == {STAR, COMPLEMENT, PREMIUM_NICHE}
    assert report["k"] == 3


def test_profile_shares_add_up(metrics: pd.DataFrame) -> None:
    _, _, report = segment_products(metrics)
    profiles = report["profiles"]
    assert sum(profile["products"] for profile in profiles) == len(metrics)
    assert sum(profile["revenue_share"] for profile in profiles) == pytest.approx(1.0)
    assert sum(profile["units_share"] for profile in profiles) == pytest.approx(1.0)


def test_silhouette_is_reported_for_candidate_k_values(metrics: pd.DataFrame) -> None:
    _, _, report = segment_products(metrics)
    assert -1.0 <= report["silhouette"] <= 1.0
    assert [row["k"] for row in report["k_evaluation"]][0] == 2.0


def test_premium_products_land_in_premium_niche(metrics: pd.DataFrame) -> None:
    _, assigned, _ = segment_products(metrics)
    premium = assigned[assigned["avg_price"] > 15]
    assert (premium["segment"] == PREMIUM_NICHE).all()


def test_classify_places_new_product_in_expected_segment(metrics: pd.DataFrame) -> None:
    model, _, _ = segment_products(metrics)
    assert model.classify(units=100, revenue=2500, avg_price=22) == PREMIUM_NICHE
    top = metrics.sort_values("units").iloc[-1]
    assert model.classify(top["units"], top["revenue"], top["avg_price"]) == STAR


def test_segmentation_is_deterministic(metrics: pd.DataFrame) -> None:
    _, first, _ = segment_products(metrics)
    _, second, _ = segment_products(metrics)
    assert first["segment"].tolist() == second["segment"].tolist()
