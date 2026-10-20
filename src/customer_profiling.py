"""
src/customer_profiling.py
─────────────────────────
Helpers for building rich per-customer profile views used on the
Customer Profiles dashboard page.
"""

from __future__ import annotations

import pandas as pd


def get_customer_profile(
    customer_id: int,
    customer_features: pd.DataFrame,
    clean_df: pd.DataFrame,
    segment_labels: dict[int, str] | None = None,
    churn_proba: float | None = None,
    next_purchase_days: float | None = None,
) -> dict:
    """
    Build a comprehensive profile dict for a single customer.

    Parameters
    ----------
    customer_id : int
    customer_features : pd.DataFrame
        Output of ``build_customer_features``.
    clean_df : pd.DataFrame
        Full cleaned DataFrame (includes cancelled rows).
    segment_labels : dict | None
        Maps CustomerID → segment name string.
    churn_proba : float | None
        Churn probability from the churn model (0-1).
    next_purchase_days : float | None
        Predicted days until next purchase.

    Returns
    -------
    dict with keys:
        metrics, orders, top_products, segment, churn_proba, next_purchase_days
    """
    row = customer_features[customer_features["CustomerID"] == customer_id]
    if row.empty:
        return {}

    metrics = row.iloc[0].to_dict()

    # All valid purchases for this customer
    purchases = clean_df[
        (clean_df["CustomerID"] == customer_id) & (~clean_df["is_cancelled"])
    ].copy()

    orders = get_customer_orders(purchases)
    top_products = _top_products(purchases)

    profile = {
        "metrics": metrics,
        "orders": orders,
        "top_products": top_products,
        "segment": segment_labels.get(customer_id) if segment_labels else None,
        "churn_proba": churn_proba,
        "next_purchase_days": next_purchase_days,
    }
    return profile


def get_customer_orders(purchase_df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarise purchase_df (non-cancelled rows for one customer) into an
    invoice-level table sorted by date descending.
    """
    if purchase_df.empty:
        return pd.DataFrame(
            columns=["InvoiceNo", "InvoiceDate", "Items", "Revenue"]
        )

    inv = (
        purchase_df.groupby(["InvoiceNo", "InvoiceDate"])
        .agg(Items=("Quantity", "sum"), Revenue=("Revenue", "sum"))
        .reset_index()
        .sort_values("InvoiceDate", ascending=False)
    )
    return inv


def _top_products(purchase_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Return the top N most-purchased products (by quantity) for a customer."""
    if purchase_df.empty:
        return pd.DataFrame(columns=["StockCode", "Description", "Quantity", "Revenue"])

    top = (
        purchase_df.groupby(["StockCode", "Description"])
        .agg(Quantity=("Quantity", "sum"), Revenue=("Revenue", "sum"))
        .reset_index()
        .sort_values("Quantity", ascending=False)
        .head(top_n)
    )
    return top


def search_customers(
    query: str,
    customer_features: pd.DataFrame,
) -> list[int]:
    """
    Return a list of CustomerIDs matching a text or numeric query.
    """
    try:
        cid = int(query)
        matches = customer_features[customer_features["CustomerID"] == cid]["CustomerID"].tolist()
    except ValueError:
        matches = customer_features["CustomerID"].tolist()
    return matches


def build_downloadable_profiles(
    customer_features: pd.DataFrame,
    segment_labels: dict[int, str] | None = None,
    churn_probas: dict[int, float] | None = None,
    next_purchase_preds: dict[int, float] | None = None,
) -> pd.DataFrame:
    """
    Merge customer features with segment labels and predictions into a
    single CSV-downloadable DataFrame.
    """
    df = customer_features.copy()
    if segment_labels:
        df["segment"] = df["CustomerID"].map(segment_labels)
    if churn_probas:
        df["churn_probability"] = df["CustomerID"].map(churn_probas)
    if next_purchase_preds:
        df["predicted_days_to_next_purchase"] = df["CustomerID"].map(next_purchase_preds)
    return df
