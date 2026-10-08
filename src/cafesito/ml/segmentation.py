from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

FEATURES = ["units", "revenue", "avg_price"]
STAR = "star"
COMPLEMENT = "complement"
PREMIUM_NICHE = "premium_niche"


@dataclass
class SegmentationModel:
    scaler: StandardScaler
    kmeans: KMeans
    names: dict[int, str]

    def classify(self, units: float, revenue: float, avg_price: float) -> str:
        point = pd.DataFrame([[units, revenue, avg_price]], columns=FEATURES)
        cluster = int(self.kmeans.predict(self.scaler.transform(point))[0])
        return self.names[cluster]


def name_clusters(centers: pd.DataFrame) -> dict[int, str]:
    if len(centers) != 3:
        return {int(index): f"segment_{index}" for index in centers.index.tolist()}
    cluster_ids = [int(index) for index in centers.index.tolist()]
    units = dict(zip(cluster_ids, centers["units"].to_numpy(dtype=float).tolist(), strict=True))
    prices = dict(
        zip(cluster_ids, centers["avg_price"].to_numpy(dtype=float).tolist(), strict=True)
    )
    ordered = sorted(cluster_ids, key=lambda cluster: units[cluster], reverse=True)
    star = ordered[0]
    premium = max(ordered[1:], key=lambda cluster: prices[cluster])
    complement = next(cluster for cluster in ordered[1:] if cluster != premium)
    return {star: STAR, complement: COMPLEMENT, premium: PREMIUM_NICHE}


def evaluate_k_values(
    scaled: np.ndarray[Any, Any], k_values: range, seed: int
) -> list[dict[str, float]]:
    results: list[dict[str, float]] = []
    for k in k_values:
        candidate = KMeans(n_clusters=k, n_init=10, random_state=seed).fit(scaled)
        results.append(
            {
                "k": float(k),
                "inertia": float(candidate.inertia_),
                "silhouette": float(silhouette_score(scaled, candidate.labels_)),
            }
        )
    return results


def segment_products(
    metrics: pd.DataFrame, k: int = 3, seed: int = 42
) -> tuple[SegmentationModel, pd.DataFrame, dict[str, Any]]:
    scaler = StandardScaler()
    scaled = scaler.fit_transform(metrics[FEATURES])
    kmeans = KMeans(n_clusters=k, n_init=10, random_state=seed).fit(scaled)

    assigned = metrics.copy()
    assigned["cluster"] = kmeans.labels_
    centers = assigned.groupby("cluster")[FEATURES].mean()
    names = name_clusters(centers)
    assigned["segment"] = assigned["cluster"].map(names)

    total_units = float(assigned["units"].sum())
    total_revenue = float(assigned["revenue"].sum())
    profiles: list[dict[str, Any]] = []
    for cluster, name in names.items():
        members = assigned[assigned["cluster"] == cluster]
        profiles.append(
            {
                "segment": name,
                "products": len(members),
                "avg_units": float(members["units"].mean()),
                "avg_revenue": float(members["revenue"].mean()),
                "avg_price": float(members["avg_price"].mean()),
                "units_share": float(members["units"].sum() / total_units),
                "revenue_share": float(members["revenue"].sum() / total_revenue),
            }
        )
    profiles.sort(key=lambda profile: profile["avg_revenue"], reverse=True)

    report = {
        "k": k,
        "silhouette": float(silhouette_score(scaled, kmeans.labels_)),
        "inertia": float(kmeans.inertia_),
        "k_evaluation": evaluate_k_values(scaled, range(2, min(7, len(metrics))), seed),
        "profiles": profiles,
    }
    return SegmentationModel(scaler=scaler, kmeans=kmeans, names=names), assigned, report
