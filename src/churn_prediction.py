"""
src/churn_prediction.py
───────────────────────
Binary classification: will a customer churn (not purchase again within
a configurable window)?

Temporal construction (no data leakage)
─────────────────────────────────────────
1. Choose a cutoff date C  (default: max_date - churn_window - buffer).
2. Build FEATURES from purchases on or before C.
3. Build LABEL from purchases after C but within the observation window.
4. Customers whose observation window extends past max_date are excluded
   (their window is incomplete → unknown ground truth).
5. The train/test split is chronological on the cutoff date dimension.

Models
───────
  • Logistic Regression (baseline)
  • Random Forest Classifier (primary)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_class_weight

from config import (
    CHURN_CUTOFF_BUFFER_DAYS,
    DEFAULT_CHURN_WINDOW_DAYS,
    MODELS_DIR,
    RANDOM_SEED,
    TRAIN_FRACTION,
)

logger = logging.getLogger(__name__)

CHURN_FEATURES = [
    "recency_at_cutoff",
    "frequency_at_cutoff",
    "monetary_at_cutoff",
    "avg_order_value_at_cutoff",
    "unique_products_at_cutoff",
    "tenure_at_cutoff",
    "mean_gap_days",
    "days_since_first",
]


@dataclass
class ChurnResult:
    best_model_name: str
    best_pipeline: Optional[Pipeline]
    lr_pipeline: Optional[Pipeline]
    rf_pipeline: Optional[Pipeline]
    test_labels: np.ndarray
    lr_predictions: np.ndarray
    rf_predictions: np.ndarray
    best_predictions: np.ndarray
    best_probas: np.ndarray
    lr_auc: float
    rf_auc: float
    lr_report: dict
    rf_report: dict
    confusion: np.ndarray
    feature_importances: Optional[pd.Series]
    churn_rate: float
    training_samples: int
    test_samples: int
    churn_window_days: int
    cutoff_date: str
    notes: list[str]
    feature_names: list[str]


def _build_churn_examples(
    purchase_df: pd.DataFrame,
    churn_window_days: int = DEFAULT_CHURN_WINDOW_DAYS,
    cutoff_buffer_days: int = CHURN_CUTOFF_BUFFER_DAYS,
) -> pd.DataFrame:
    """
    Construct labelled churn examples using a single-cutoff approach.
    """
    purchase_df = purchase_df.copy()
    purchase_df["InvoiceDate"] = pd.to_datetime(purchase_df["InvoiceDate"])

    max_date = purchase_df["InvoiceDate"].max()
    # Customers need at least `buffer` days of observation window
    cutoff_date = max_date - pd.Timedelta(days=churn_window_days + cutoff_buffer_days)

    if cutoff_date <= purchase_df["InvoiceDate"].min():
        return pd.DataFrame()  # not enough data

    # Split purchases
    before = purchase_df[purchase_df["InvoiceDate"] <= cutoff_date]
    after_window = purchase_df[
        (purchase_df["InvoiceDate"] > cutoff_date)
        & (purchase_df["InvoiceDate"] <= cutoff_date + pd.Timedelta(days=churn_window_days))
    ]

    if before.empty:
        return pd.DataFrame()

    # Build features from 'before' data
    inv_before = (
        before.groupby(["CustomerID", "InvoiceNo"])
        .agg(
            date=("InvoiceDate", "max"),
            revenue=("Revenue", "sum"),
            n_products=("StockCode", "nunique"),
        )
        .reset_index()
        .sort_values(["CustomerID", "date"])
    )

    feats = []
    for cid, grp in inv_before.groupby("CustomerID"):
        grp = grp.sort_values("date")
        last_date = grp["date"].max()
        first_date = grp["date"].min()
        gaps = grp["date"].diff().dt.days.dropna()

        feats.append({
            "CustomerID": cid,
            "recency_at_cutoff": (cutoff_date - last_date).days,
            "frequency_at_cutoff": len(grp),
            "monetary_at_cutoff": grp["revenue"].sum(),
            "avg_order_value_at_cutoff": grp["revenue"].mean(),
            "unique_products_at_cutoff": grp["n_products"].sum(),
            "tenure_at_cutoff": (last_date - first_date).days,
            "mean_gap_days": gaps.mean() if len(gaps) > 0 else 0.0,
            "days_since_first": (cutoff_date - first_date).days,
        })

    feat_df = pd.DataFrame(feats)

    # Build labels: churned = 1 if no purchase in window after cutoff
    active_after = set(after_window["CustomerID"].unique())
    feat_df["churned"] = (~feat_df["CustomerID"].isin(active_after)).astype(int)
    feat_df["cutoff_date"] = cutoff_date

    return feat_df


def train_churn_model(
    purchase_df: pd.DataFrame,
    churn_window_days: int = DEFAULT_CHURN_WINDOW_DAYS,
) -> ChurnResult:
    """
    Train and evaluate churn prediction models.

    Parameters
    ----------
    purchase_df : pd.DataFrame
        Valid (non-cancelled) purchases.
    churn_window_days : int
        Number of days without purchase to define churn.

    Returns
    -------
    ChurnResult
    """
    notes = []
    examples = _build_churn_examples(purchase_df, churn_window_days)

    if examples.empty or len(examples) < 50:
        msg = (
            f"Insufficient data for churn model "
            f"(only {len(examples)} examples). "
            "Churn prediction disabled."
        )
        logger.warning(msg)
        notes.append(msg)
        return ChurnResult(
            best_model_name="N/A",
            best_pipeline=None,
            lr_pipeline=None,
            rf_pipeline=None,
            test_labels=np.array([]),
            lr_predictions=np.array([]),
            rf_predictions=np.array([]),
            best_predictions=np.array([]),
            best_probas=np.array([]),
            lr_auc=np.nan,
            rf_auc=np.nan,
            lr_report={},
            rf_report={},
            confusion=np.array([]),
            feature_importances=None,
            churn_rate=np.nan,
            training_samples=0,
            test_samples=0,
            churn_window_days=churn_window_days,
            cutoff_date="N/A",
            notes=notes,
            feature_names=[],
        )

    feat_cols = [c for c in CHURN_FEATURES if c in examples.columns]
    churn_rate = float(examples["churned"].mean())
    cutoff_date = str(examples["cutoff_date"].iloc[0].date())

    # Chronological split (by recency_at_cutoff as proxy for "time of observation")
    examples = examples.sort_values("recency_at_cutoff").reset_index(drop=True)
    split = int(len(examples) * TRAIN_FRACTION)
    train = examples.iloc[:split]
    test = examples.iloc[split:]

    X_train = train[feat_cols].fillna(0)
    y_train = train["churned"]
    X_test = test[feat_cols].fillna(0)
    y_test = test["churned"]

    if len(X_test) == 0:
        X_test, y_test = X_train, y_train

    # Class weights for imbalance
    classes = np.array([0, 1])
    weights = compute_class_weight("balanced", classes=classes, y=y_train)
    class_weight = {0: weights[0], 1: weights[1]}

    # ── Logistic Regression ──────────────────────────────────────────────────
    lr_pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(
            max_iter=1000,
            class_weight=class_weight,
            random_state=RANDOM_SEED,
        )),
    ])
    lr_pipe.fit(X_train, y_train)
    lr_preds = lr_pipe.predict(X_test)
    lr_probas = lr_pipe.predict_proba(X_test)[:, 1]
    lr_auc = roc_auc_score(y_test, lr_probas) if len(np.unique(y_test)) > 1 else np.nan
    lr_report = classification_report(y_test, lr_preds, output_dict=True)

    # ── Random Forest ────────────────────────────────────────────────────────
    rf_pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("model", RandomForestClassifier(
            n_estimators=200,
            max_depth=8,
            class_weight=class_weight,
            random_state=RANDOM_SEED,
            n_jobs=-1,
        )),
    ])
    rf_pipe.fit(X_train, y_train)
    rf_preds = rf_pipe.predict(X_test)
    rf_probas = rf_pipe.predict_proba(X_test)[:, 1]
    rf_auc = roc_auc_score(y_test, rf_probas) if len(np.unique(y_test)) > 1 else np.nan
    rf_report = classification_report(y_test, rf_preds, output_dict=True)

    # Choose best by AUC
    if (not np.isnan(rf_auc)) and rf_auc >= lr_auc:
        best_name = "Random Forest"
        best_pipe = rf_pipe
        best_preds = rf_preds
        best_probas = rf_probas
        importances = pd.Series(
            rf_pipe.named_steps["model"].feature_importances_,
            index=feat_cols,
        ).sort_values(ascending=False)
    else:
        best_name = "Logistic Regression"
        best_pipe = lr_pipe
        best_preds = lr_preds
        best_probas = lr_probas
        importances = pd.Series(
            np.abs(lr_pipe.named_steps["model"].coef_[0]),
            index=feat_cols,
        ).sort_values(ascending=False)

    conf = confusion_matrix(y_test, best_preds)
    notes.append(f"Churn window: {churn_window_days} days.")
    notes.append(f"Cutoff date: {cutoff_date}.")
    notes.append(f"Overall churn rate: {churn_rate:.1%}.")
    notes.append(
        "Probabilities are model estimates, not guarantees. "
        "Treat high-probability customers as at-risk, not confirmed churners."
    )

    logger.info(
        "Churn model — Best=%s, LR AUC=%.3f, RF AUC=%.3f",
        best_name, lr_auc, rf_auc,
    )

    return ChurnResult(
        best_model_name=best_name,
        best_pipeline=best_pipe,
        lr_pipeline=lr_pipe,
        rf_pipeline=rf_pipe,
        test_labels=y_test.values,
        lr_predictions=lr_preds,
        rf_predictions=rf_preds,
        best_predictions=best_preds,
        best_probas=best_probas,
        lr_auc=lr_auc,
        rf_auc=rf_auc,
        lr_report=lr_report,
        rf_report=rf_report,
        confusion=conf,
        feature_importances=importances,
        churn_rate=churn_rate,
        training_samples=len(train),
        test_samples=len(test),
        churn_window_days=churn_window_days,
        cutoff_date=cutoff_date,
        notes=notes,
        feature_names=feat_cols,
    )


def predict_churn(
    customer_id: int,
    purchase_df: pd.DataFrame,
    result: ChurnResult,
) -> Optional[float]:
    """
    Return the estimated churn probability for a single customer.
    Returns None if the model is unavailable.
    """
    if result.best_pipeline is None:
        return None

    cust_df = purchase_df[purchase_df["CustomerID"] == customer_id].copy()
    cust_df["InvoiceDate"] = pd.to_datetime(cust_df["InvoiceDate"])
    if cust_df.empty:
        return None

    max_date = purchase_df["InvoiceDate"].max()
    inv = (
        cust_df.groupby("InvoiceNo")
        .agg(
            date=("InvoiceDate", "max"),
            revenue=("Revenue", "sum"),
            n_products=("StockCode", "nunique"),
        )
        .reset_index()
        .sort_values("date")
    )

    gaps = inv["date"].diff().dt.days.dropna()
    last_date = inv["date"].max()
    first_date = inv["date"].min()

    feat = {
        "recency_at_cutoff": (max_date - last_date).days,
        "frequency_at_cutoff": len(inv),
        "monetary_at_cutoff": inv["revenue"].sum(),
        "avg_order_value_at_cutoff": inv["revenue"].mean(),
        "unique_products_at_cutoff": inv["n_products"].sum(),
        "tenure_at_cutoff": (last_date - first_date).days,
        "mean_gap_days": gaps.mean() if len(gaps) > 0 else 0.0,
        "days_since_first": (max_date - first_date).days,
    }

    feat_cols = [c for c in result.feature_names if c in feat]
    X = pd.DataFrame([feat])[feat_cols].fillna(0)

    try:
        proba = float(result.best_pipeline.predict_proba(X)[0, 1])
        return proba
    except Exception as exc:
        logger.warning("Churn prediction failed for customer %s: %s", customer_id, exc)
        return None


def churn_risk_category(proba: float) -> str:
    """Map a probability to a human-readable risk tier."""
    if proba >= 0.75:
        return "High Risk"
    elif proba >= 0.45:
        return "Medium Risk"
    else:
        return "Low Risk"


def save_churn_model(result: ChurnResult, path: Optional[str] = None) -> str:
    import os
    path = path or os.path.join(MODELS_DIR, "churn_model.joblib")
    joblib.dump(result, path)
    return path


def load_churn_model(path: Optional[str] = None) -> ChurnResult:
    import os
    path = path or os.path.join(MODELS_DIR, "churn_model.joblib")
    return joblib.load(path)
