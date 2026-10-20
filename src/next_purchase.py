"""
src/next_purchase.py
────────────────────
Predicts how many days until a customer's NEXT purchase.

Training strategy (no data leakage)
────────────────────────────────────
For each customer with ≥ MIN_INVOICES_FOR_PREDICTION valid invoices:
  • Sort purchases chronologically.
  • Create one training example per purchase (excluding the last):
      – Target   : days until the NEXT purchase (forward gap).
      – Features : aggregated from all purchases UP TO AND INCLUDING the current one.
  • Split examples by their observation date (chronological split), NOT randomly.

Baseline
────────
The baseline predicts the customer's mean historical inter-order gap at the
time of prediction.  This is a strong, realistic baseline for sparse data.

Models compared
───────────────
  1. Baseline (mean inter-order gap)
  2. Random Forest Regressor
  3. Gradient Boosted Trees (HistGradientBoostingRegressor)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import (
    MIN_INVOICES_FOR_PREDICTION,
    MODELS_DIR,
    RANDOM_SEED,
    TRAIN_FRACTION,
    VALIDATION_FRACTION,
)

logger = logging.getLogger(__name__)

NEXT_PURCHASE_FEATURES = [
    "n_prior_orders",
    "mean_gap_days",
    "std_gap_days",
    "min_gap_days",
    "max_gap_days",
    "recency_days",
    "cum_revenue",
    "avg_revenue",
    "unique_products_so_far",
    "tenure_days",
    "order_index",          # position of this purchase in customer history
]


@dataclass
class NextPurchaseResult:
    best_model_name: str
    best_pipeline: Optional[Pipeline]
    baseline_mae: float
    baseline_rmse: float
    model_mae: float
    model_rmse: float
    val_mae: float
    val_rmse: float
    feature_importances: Optional[pd.Series]
    training_samples: int
    test_samples: int
    notes: list[str]


def _build_training_examples(purchase_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create one training row per (customer, purchase) pair where a next
    purchase exists.  Uses only information available at prediction time.
    """
    purchase_df = purchase_df.copy()
    purchase_df["InvoiceDate"] = pd.to_datetime(purchase_df["InvoiceDate"])

    # Deduplicate to invoice level (take max date per invoice)
    inv = (
        purchase_df.groupby(["CustomerID", "InvoiceNo"])
        .agg(
            date=("InvoiceDate", "max"),
            revenue=("Revenue", "sum"),
            qty=("Quantity", "sum"),
            n_products=("StockCode", "nunique"),
        )
        .reset_index()
        .sort_values(["CustomerID", "date"])
    )

    # Filter to customers with sufficient history
    counts = inv.groupby("CustomerID")["InvoiceNo"].count()
    eligible = counts[counts >= MIN_INVOICES_FOR_PREDICTION].index
    inv = inv[inv["CustomerID"].isin(eligible)]

    rows = []
    for cid, grp in inv.groupby("CustomerID"):
        grp = grp.sort_values("date").reset_index(drop=True)
        n = len(grp)
        for i in range(n - 1):          # exclude last (no future)
            history = grp.iloc[: i + 1]
            current = grp.iloc[i]
            next_purchase = grp.iloc[i + 1]
            target = (next_purchase["date"] - current["date"]).days

            if target <= 0:             # same-day edge case
                continue

            gaps = history["date"].diff().dt.days.dropna()
            cum_revenue = history["revenue"].sum()

            rows.append({
                "CustomerID": cid,
                "observation_date": current["date"],
                "target_days": target,
                "n_prior_orders": i + 1,
                "mean_gap_days": gaps.mean() if len(gaps) > 0 else 0.0,
                "std_gap_days": gaps.std() if len(gaps) > 0 else 0.0,
                "min_gap_days": gaps.min() if len(gaps) > 0 else 0.0,
                "max_gap_days": gaps.max() if len(gaps) > 0 else 0.0,
                "recency_days": 0,       # 0 at prediction time (just purchased)
                "cum_revenue": cum_revenue,
                "avg_revenue": cum_revenue / (i + 1),
                "unique_products_so_far": history["n_products"].sum(),
                "tenure_days": (current["date"] - history["date"].min()).days,
                "order_index": i + 1,
            })

    return pd.DataFrame(rows)


def train_next_purchase_model(
    purchase_df: pd.DataFrame,
) -> NextPurchaseResult:
    """
    Build and evaluate the next-purchase prediction model.

    Parameters
    ----------
    purchase_df : pd.DataFrame
        Valid (non-cancelled) purchase rows.

    Returns
    -------
    NextPurchaseResult
    """
    notes = []
    examples = _build_training_examples(purchase_df)

    if len(examples) < 50:
        msg = (
            f"Only {len(examples)} training examples generated "
            f"(need ≥ 50 and customers with ≥ {MIN_INVOICES_FOR_PREDICTION} invoices). "
            "Next-purchase prediction disabled."
        )
        logger.warning(msg)
        notes.append(msg)
        return NextPurchaseResult(
            best_model_name="N/A",
            best_pipeline=None,
            baseline_mae=np.nan,
            baseline_rmse=np.nan,
            model_mae=np.nan,
            model_rmse=np.nan,
            val_mae=np.nan,
            val_rmse=np.nan,
            feature_importances=None,
            training_samples=0,
            test_samples=0,
            notes=notes,
        )

    # Chronological split
    examples = examples.sort_values("observation_date").reset_index(drop=True)
    n = len(examples)
    train_end = int(n * TRAIN_FRACTION)
    val_end = int(n * (TRAIN_FRACTION + VALIDATION_FRACTION))

    train = examples.iloc[:train_end]
    val = examples.iloc[train_end:val_end]
    test = examples.iloc[val_end:]

    feat_cols = [c for c in NEXT_PURCHASE_FEATURES if c in examples.columns]

    X_train = train[feat_cols].fillna(0)
    y_train = train["target_days"]
    X_val = val[feat_cols].fillna(0)
    y_val = val["target_days"]
    X_test = test[feat_cols].fillna(0)
    y_test = test["target_days"]

    if len(X_test) == 0 or len(X_val) == 0:
        notes.append("Not enough data for a proper train/val/test split. Using train as test.")
        X_test, y_test = X_train, y_train
        X_val, y_val = X_train, y_train

    # ── Baseline: predict mean_gap_days for each row ─────────────────────────
    baseline_preds = X_test["mean_gap_days"].clip(lower=1).values
    baseline_mae = mean_absolute_error(y_test, baseline_preds)
    baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_preds))

    # ── Random Forest ────────────────────────────────────────────────────────
    rf_pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("model", RandomForestRegressor(
            n_estimators=200,
            max_depth=8,
            min_samples_leaf=5,
            random_state=RANDOM_SEED,
            n_jobs=-1,
        )),
    ])
    rf_pipe.fit(X_train, y_train)
    rf_val_preds = rf_pipe.predict(X_val)
    rf_val_mae = mean_absolute_error(y_val, rf_val_preds)
    rf_test_preds = rf_pipe.predict(X_test)
    rf_mae = mean_absolute_error(y_test, rf_test_preds)
    rf_rmse = np.sqrt(mean_squared_error(y_test, rf_test_preds))

    # ── Gradient Boosting ────────────────────────────────────────────────────
    gb_pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("model", GradientBoostingRegressor(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            random_state=RANDOM_SEED,
        )),
    ])
    gb_pipe.fit(X_train, y_train)
    gb_val_preds = gb_pipe.predict(X_val)
    gb_val_mae = mean_absolute_error(y_val, gb_val_preds)
    gb_test_preds = gb_pipe.predict(X_test)
    gb_mae = mean_absolute_error(y_test, gb_test_preds)
    gb_rmse = np.sqrt(mean_squared_error(y_test, gb_test_preds))

    # Choose best model by validation MAE
    if rf_val_mae <= gb_val_mae:
        best_name = "Random Forest"
        best_pipe = rf_pipe
        best_mae, best_rmse = rf_mae, rf_rmse
        best_val_mae = rf_val_mae
        importances = pd.Series(
            rf_pipe.named_steps["model"].feature_importances_,
            index=feat_cols,
        ).sort_values(ascending=False)
    else:
        best_name = "Gradient Boosting"
        best_pipe = gb_pipe
        best_mae, best_rmse = gb_mae, gb_rmse
        best_val_mae = gb_val_mae
        importances = pd.Series(
            gb_pipe.named_steps["model"].feature_importances_,
            index=feat_cols,
        ).sort_values(ascending=False)

    notes.append(
        f"Training examples: {len(train):,} | Validation: {len(val):,} | Test: {len(test):,}."
    )
    notes.append(
        "Chronological split used — no future data leaks into training features."
    )
    notes.append(
        "Limitation: sparse purchase history makes precise day-level prediction difficult. "
        "Use predictions as order-of-magnitude estimates."
    )

    logger.info(
        "Next-purchase — Best=%s, Test MAE=%.1f days, RMSE=%.1f days, "
        "Baseline MAE=%.1f days",
        best_name, best_mae, best_rmse, baseline_mae,
    )

    return NextPurchaseResult(
        best_model_name=best_name,
        best_pipeline=best_pipe,
        baseline_mae=baseline_mae,
        baseline_rmse=baseline_rmse,
        model_mae=best_mae,
        model_rmse=best_rmse,
        val_mae=best_val_mae,
        val_rmse=np.sqrt(mean_squared_error(y_val, best_pipe.predict(X_val))),
        feature_importances=importances,
        training_samples=len(train),
        test_samples=len(test),
        notes=notes,
    )


def predict_next_purchase(
    customer_id: int,
    purchase_df: pd.DataFrame,
    result: NextPurchaseResult,
) -> Optional[float]:
    """
    Predict days until the next purchase for a given customer.

    Returns None if the model is not available or the customer has
    insufficient history.
    """
    if result.best_pipeline is None:
        return None

    purchase_df = purchase_df[purchase_df["CustomerID"] == customer_id].copy()
    purchase_df["InvoiceDate"] = pd.to_datetime(purchase_df["InvoiceDate"])

    inv = (
        purchase_df.groupby("InvoiceNo")
        .agg(
            date=("InvoiceDate", "max"),
            revenue=("Revenue", "sum"),
            n_products=("StockCode", "nunique"),
        )
        .reset_index()
        .sort_values("date")
    )

    if len(inv) < 1:
        return None

    history = inv
    gaps = history["date"].diff().dt.days.dropna()
    cum_revenue = history["revenue"].sum()
    n = len(history)

    feat = {
        "n_prior_orders": n,
        "mean_gap_days": gaps.mean() if len(gaps) > 0 else 0.0,
        "std_gap_days": gaps.std() if len(gaps) > 0 else 0.0,
        "min_gap_days": gaps.min() if len(gaps) > 0 else 0.0,
        "max_gap_days": gaps.max() if len(gaps) > 0 else 0.0,
        "recency_days": 0,
        "cum_revenue": cum_revenue,
        "avg_revenue": cum_revenue / n,
        "unique_products_so_far": history["n_products"].sum(),
        "tenure_days": (history["date"].iloc[-1] - history["date"].iloc[0]).days,
        "order_index": n,
    }

    feat_cols = [c for c in NEXT_PURCHASE_FEATURES if c in feat]
    X = pd.DataFrame([feat])[feat_cols].fillna(0)

    try:
        pred = float(result.best_pipeline.predict(X)[0])
        return max(1.0, pred)
    except Exception as exc:
        logger.warning("Prediction failed for customer %s: %s", customer_id, exc)
        return None


def save_next_purchase_model(result: NextPurchaseResult, path: Optional[str] = None) -> str:
    import os
    path = path or os.path.join(MODELS_DIR, "next_purchase_model.joblib")
    joblib.dump(result, path)
    return path


def load_next_purchase_model(path: Optional[str] = None) -> NextPurchaseResult:
    import os
    path = path or os.path.join(MODELS_DIR, "next_purchase_model.joblib")
    return joblib.load(path)
