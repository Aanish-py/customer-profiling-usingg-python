"""
src/feature_engineering.py
──────────────────────────
Builds one row per customer containing all features used by downstream ML
models.  All aggregations use only valid (non-cancelled) purchase rows so
that returns do not inflate frequency or monetary figures.

Feature definitions
───────────────────
recency          – Days between the customer's last purchase and the reference
                   date (dataset max date by default).  Lower = more recent.
frequency        – Count of distinct valid purchase InvoiceNo values.
monetary         – Net spending: sum of Revenue for valid purchases only.
avg_order_value  – monetary / frequency.
avg_qty_per_order– Mean Quantity per valid invoice.
unique_products  – Count of distinct StockCode values in valid purchases.
tenure_days      – Days between the customer's first and last purchase.
repeat_rate      – 1 if frequency > 1 else 0.
inter_order_days – Mean days between consecutive purchases (NaN if frequency < 2).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from config import RANDOM_SEED


def build_customer_features(
    purchase_df: pd.DataFrame,
    reference_date: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """
    Aggregate valid (non-cancelled) purchase rows into one row per customer.

    Parameters
    ----------
    purchase_df : pd.DataFrame
        Must contain only NON-cancelled rows (is_cancelled == False).
        Expected columns: CustomerID, InvoiceNo, InvoiceDate, StockCode,
                          Quantity, UnitPrice, Revenue.
    reference_date : pd.Timestamp | None
        Date used to compute recency.  Defaults to the latest InvoiceDate in
        the dataset so results are reproducible regardless of when the script runs.

    Returns
    -------
    pd.DataFrame
        One row per CustomerID.  Index is reset.
    """
    if reference_date is None:
        reference_date = purchase_df["InvoiceDate"].max()

    # Ensure InvoiceDate is datetime
    purchase_df = purchase_df.copy()
    purchase_df["InvoiceDate"] = pd.to_datetime(purchase_df["InvoiceDate"])

    # Invoice-level aggregation first (group by customer + invoice)
    inv_agg = (
        purchase_df.groupby(["CustomerID", "InvoiceNo"])
        .agg(
            invoice_date=("InvoiceDate", "max"),
            invoice_revenue=("Revenue", "sum"),
            invoice_qty=("Quantity", "sum"),
        )
        .reset_index()
    )

    # Customer-level aggregation
    cust_inv = (
        inv_agg.groupby("CustomerID")
        .agg(
            first_purchase=("invoice_date", "min"),
            last_purchase=("invoice_date", "max"),
            frequency=("InvoiceNo", "nunique"),
            monetary=("invoice_revenue", "sum"),
            avg_order_value=("invoice_revenue", "mean"),
            avg_qty_per_order=("invoice_qty", "mean"),
        )
        .reset_index()
    )

    cust_inv["recency"] = (
        reference_date - cust_inv["last_purchase"]
    ).dt.days.clip(lower=0)

    cust_inv["tenure_days"] = (
        cust_inv["last_purchase"] - cust_inv["first_purchase"]
    ).dt.days.clip(lower=0)

    cust_inv["repeat_rate"] = (cust_inv["frequency"] > 1).astype(int)

    # Unique products
    prod_counts = (
        purchase_df.groupby("CustomerID")["StockCode"]
        .nunique()
        .reset_index()
        .rename(columns={"StockCode": "unique_products"})
    )
    cust_inv = cust_inv.merge(prod_counts, on="CustomerID", how="left")

    # Mean inter-order gap (days between consecutive purchases)
    inter_order_series = _mean_inter_order_days(inv_agg)
    inter_order_df = inter_order_series.reset_index()
    inter_order_df.columns = ["CustomerID", "inter_order_days"]
    cust_inv = cust_inv.merge(inter_order_df, on="CustomerID", how="left")

    # Country (mode)
    if "Country" in purchase_df.columns:
        country_mode = (
            purchase_df.groupby("CustomerID")["Country"]
            .agg(lambda x: x.mode().iloc[0] if len(x) > 0 else "Unknown")
            .reset_index()
            .rename(columns={"Country": "country"})
        )
        cust_inv = cust_inv.merge(country_mode, on="CustomerID", how="left")

    cust_inv["reference_date"] = reference_date

    return cust_inv.reset_index(drop=True)


def _mean_inter_order_days(inv_agg: pd.DataFrame) -> pd.Series:
    """
    Compute the mean number of days between consecutive invoices per customer.
    Returns a Series indexed by CustomerID. NaN for customers with only one invoice.
    """
    inv_sorted = inv_agg.sort_values(["CustomerID", "invoice_date"])
    gaps = (
        inv_sorted.groupby("CustomerID")["invoice_date"]
        .apply(lambda dates: dates.diff().dt.days.dropna().mean())
    )
    # gaps is already indexed by CustomerID
    return gaps


# ── Helper utilities ──────────────────────────────────────────────────────────

def log_transform_features(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """
    Apply log1p transformation to right-skewed columns.
    Returns a copy with new columns named ``<col>_log``.
    """
    df = df.copy()
    for col in columns:
        df[f"{col}_log"] = np.log1p(df[col].clip(lower=0))
    return df


def get_rfm_features(customer_features: pd.DataFrame) -> pd.DataFrame:
    """Return the subset of customer_features used for RFM-based modelling."""
    cols = ["CustomerID", "recency", "frequency", "monetary",
            "avg_order_value", "avg_qty_per_order", "unique_products",
            "tenure_days", "repeat_rate", "inter_order_days"]
    available = [c for c in cols if c in customer_features.columns]
    return customer_features[available].copy()
