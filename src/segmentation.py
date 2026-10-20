"""
src/segmentation.py
───────────────────
K-Means customer segmentation using RFM+ features.

Workflow
────────
1. Select and log-transform skewed features.
2. Scale with StandardScaler.
3. Sweep K from KMEANS_CLUSTER_RANGE using elbow (inertia) and silhouette score.
4. Fit final model with the chosen K.
5. Reduce to 2-D with PCA for visualisation.
6. Name segments after examining cluster centroids.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import (
    DEFAULT_N_CLUSTERS,
    KMEANS_CLUSTER_RANGE,
    MODELS_DIR,
    RANDOM_SEED,
)

logger = logging.getLogger(__name__)

SEGMENTATION_FEATURES = [
    "recency",
    "frequency",
    "monetary",
    "avg_order_value",
    "unique_products",
    "tenure_days",
]


@dataclass
class SegmentationResult:
    pipeline: Pipeline
    n_clusters: int
    labels: np.ndarray          # cluster integer labels, aligned to input rows
    cluster_centers: pd.DataFrame
    pca_coords: np.ndarray      # (N, 2) for scatter plots
    inertias: dict[int, float]
    silhouette_scores: dict[int, float]
    segment_names: dict[int, str] = field(default_factory=dict)
    feature_names: list[str] = field(default_factory=list)


def train_segmentation(
    customer_features: pd.DataFrame,
    n_clusters: Optional[int] = None,
) -> SegmentationResult:
    """
    Fit K-Means segmentation on *customer_features*.

    Parameters
    ----------
    customer_features : pd.DataFrame
        Output of ``build_customer_features``.
    n_clusters : int | None
        If None, the best K is chosen automatically via silhouette score.

    Returns
    -------
    SegmentationResult
    """
    feat_cols = [c for c in SEGMENTATION_FEATURES if c in customer_features.columns]
    X_raw = customer_features[feat_cols].copy()

    # Log-transform skewed columns
    for col in ["monetary", "frequency", "avg_order_value", "unique_products"]:
        if col in X_raw.columns:
            X_raw[col] = np.log1p(X_raw[col].clip(lower=0))

    # Fill any remaining NaN (e.g. inter_order_days for 1-purchase customers)
    X_raw = X_raw.fillna(0)

    # Evaluate K range
    k_min, k_max = KMEANS_CLUSTER_RANGE
    inertias: dict[int, float] = {}
    sil_scores: dict[int, float] = {}

    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, random_state=RANDOM_SEED, n_init=10)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_raw)
        labels = km.fit_predict(X_scaled)
        inertias[k] = float(km.inertia_)
        if k > 1 and len(np.unique(labels)) > 1:
            sil_scores[k] = float(silhouette_score(X_scaled, labels, random_state=RANDOM_SEED))
        else:
            sil_scores[k] = -1.0

    if n_clusters is None:
        # Choose K with highest silhouette score
        n_clusters = max(sil_scores, key=sil_scores.get)
        logger.info("Auto-selected K=%d (silhouette=%.3f)", n_clusters, sil_scores[n_clusters])

    # Fit final pipeline
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("kmeans", KMeans(n_clusters=n_clusters, random_state=RANDOM_SEED, n_init=10)),
    ])
    pipeline.fit(X_raw)
    labels = pipeline.predict(X_raw)

    # Cluster centres in original (log-transformed, then unscaled) space
    X_scaled_final = pipeline.named_steps["scaler"].transform(X_raw)
    centres_scaled = pipeline.named_steps["kmeans"].cluster_centers_
    centres_original = pipeline.named_steps["scaler"].inverse_transform(centres_scaled)
    cluster_centers = pd.DataFrame(centres_original, columns=feat_cols)
    cluster_centers.index.name = "cluster"

    # PCA 2-D projection for visualisation
    pca = PCA(n_components=2, random_state=RANDOM_SEED)
    pca_coords = pca.fit_transform(X_scaled_final)

    # Assign human-readable names based on cluster characteristics
    segment_names = _name_segments(cluster_centers, n_clusters)
    logger.info("Segment names: %s", segment_names)

    result = SegmentationResult(
        pipeline=pipeline,
        n_clusters=n_clusters,
        labels=labels,
        cluster_centers=cluster_centers,
        pca_coords=pca_coords,
        inertias=inertias,
        silhouette_scores=sil_scores,
        segment_names=segment_names,
        feature_names=feat_cols,
    )
    return result


def _name_segments(centers: pd.DataFrame, n_clusters: int) -> dict[int, str]:
    """
    Assign descriptive names to clusters by ranking them on key metrics.
    Names are derived from data, not predetermined labels.
    """
    names = {}

    # Rank clusters
    has_recency = "recency" in centers.columns
    has_monetary = "monetary" in centers.columns
    has_frequency = "frequency" in centers.columns

    recency_rank = centers["recency"].rank(ascending=True) if has_recency else None   # low = good
    monetary_rank = centers["monetary"].rank(ascending=False) if has_monetary else None  # high = good
    freq_rank = centers["frequency"].rank(ascending=False) if has_frequency else None

    for i in range(n_clusters):
        r = recency_rank[i] if recency_rank is not None else n_clusters / 2
        m = monetary_rank[i] if monetary_rank is not None else n_clusters / 2
        f = freq_rank[i] if freq_rank is not None else n_clusters / 2

        score = r + m + f   # lower total = better customer

        if score <= n_clusters * 1.0:
            names[i] = "High-Value Loyalists"
        elif m <= n_clusters / 2 and f <= n_clusters / 2:
            names[i] = "Frequent Mid-Spenders"
        elif r <= n_clusters / 2:
            names[i] = "Recent Newcomers"
        elif r >= n_clusters * 0.8:
            names[i] = "At-Risk / Inactive"
        else:
            names[i] = "Occasional Buyers"

    # Deduplicate names by appending cluster index if needed
    seen: dict[str, int] = {}
    for i, name in names.items():
        if name in seen:
            seen[name] += 1
            names[i] = f"{name} {seen[name]}"
        else:
            seen[name] = 1

    return names


def assign_segments(
    customer_features: pd.DataFrame,
    result: SegmentationResult,
) -> pd.DataFrame:
    """
    Add ``cluster`` and ``segment`` columns to *customer_features*.
    Returns a copy.
    """
    feat_cols = result.feature_names
    X_raw = customer_features[feat_cols].copy()
    for col in ["monetary", "frequency", "avg_order_value", "unique_products"]:
        if col in X_raw.columns:
            X_raw[col] = np.log1p(X_raw[col].clip(lower=0))
    X_raw = X_raw.fillna(0)

    df = customer_features.copy()
    df["cluster"] = result.pipeline.predict(X_raw)
    df["segment"] = df["cluster"].map(result.segment_names)
    return df


def save_segmentation(result: SegmentationResult, path: Optional[str] = None) -> str:
    """Persist the segmentation pipeline using joblib."""
    import os
    path = path or os.path.join(MODELS_DIR, "segmentation_pipeline.joblib")
    joblib.dump(result, path)
    return path


def load_segmentation(path: Optional[str] = None) -> SegmentationResult:
    """Load a previously saved SegmentationResult."""
    import os
    path = path or os.path.join(MODELS_DIR, "segmentation_pipeline.joblib")
    return joblib.load(path)


def cluster_profile_table(
    customer_features: pd.DataFrame,
    result: SegmentationResult,
) -> pd.DataFrame:
    """
    Return a summary table: one row per cluster with mean metrics and count.
    """
    df = assign_segments(customer_features, result)
    agg_cols = {
        "recency": "mean",
        "frequency": "mean",
        "monetary": "mean",
        "avg_order_value": "mean",
        "unique_products": "mean",
        "tenure_days": "mean",
        "CustomerID": "count",
    }
    agg_cols = {k: v for k, v in agg_cols.items() if k in df.columns}
    profile = (
        df.groupby("segment")
        .agg(**{k: (k, v) for k, v in agg_cols.items()})
        .reset_index()
    )
    if "CustomerID" in profile.columns:
        profile.rename(columns={"CustomerID": "customer_count"}, inplace=True)
    return profile
