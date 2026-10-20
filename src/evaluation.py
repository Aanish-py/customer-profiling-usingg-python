"""
src/evaluation.py
─────────────────
Shared evaluation utilities used by both the ML modules and the
Model Evaluation dashboard page.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    roc_auc_score,
)


def evaluate_regressor(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_name: str = "Model",
    baseline_pred: Optional[np.ndarray] = None,
) -> pd.DataFrame:
    """
    Compute MAE and RMSE for a regression model and an optional baseline.

    Returns
    -------
    pd.DataFrame with columns: Model, MAE, RMSE
    """
    rows = []
    rows.append({
        "Model": model_name,
        "MAE": round(mean_absolute_error(y_true, y_pred), 2),
        "RMSE": round(np.sqrt(mean_squared_error(y_true, y_pred)), 2),
    })
    if baseline_pred is not None:
        rows.append({
            "Model": "Baseline",
            "MAE": round(mean_absolute_error(y_true, baseline_pred), 2),
            "RMSE": round(np.sqrt(mean_squared_error(y_true, baseline_pred)), 2),
        })
    return pd.DataFrame(rows)


def evaluate_classifier(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray] = None,
    model_name: str = "Model",
) -> dict:
    """
    Compute classification metrics.

    Returns
    -------
    dict with keys: model_name, report_df, confusion_matrix, auc
    """
    report = classification_report(y_true, y_pred, output_dict=True)
    cm = confusion_matrix(y_true, y_pred)
    auc = (
        roc_auc_score(y_true, y_proba)
        if y_proba is not None and len(np.unique(y_true)) > 1
        else np.nan
    )
    report_df = pd.DataFrame(report).T
    return {
        "model_name": model_name,
        "report_df": report_df,
        "confusion_matrix": cm,
        "auc": auc,
    }


def silhouette_summary(silhouette_scores: dict[int, float]) -> pd.DataFrame:
    """Convert silhouette scores dict to a display DataFrame."""
    return pd.DataFrame(
        [{"K": k, "Silhouette Score": round(v, 4)} for k, v in silhouette_scores.items()]
    )


def inertia_summary(inertias: dict[int, float]) -> pd.DataFrame:
    """Convert inertias dict to a display DataFrame for elbow plots."""
    return pd.DataFrame(
        [{"K": k, "Inertia (WCSS)": round(v, 2)} for k, v in inertias.items()]
    )
