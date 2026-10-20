"""
src/preprocessing.py
────────────────────
Cleans the raw UCI Online Retail DataFrame and returns a clean copy together
with a detailed PreprocessingReport that logs every decision made.

Accounting rule for Revenue
────────────────────────────
  Revenue = Quantity × UnitPrice
  • Regular invoices (InvoiceNo does NOT start with 'C'): positive lines only.
  • Cancelled invoices (InvoiceNo starts with 'C'): kept as *negative* revenue
    so analysts can inspect net-of-returns figures.  They are EXCLUDED from
    "valid purchases" used for frequency / churn / next-purchase features.
  • Lines with UnitPrice == 0 are treated as samples / test records and removed.
  • Lines with Quantity <= 0 AND InvoiceNo NOT starting with 'C' are treated as
    data errors and removed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from config import MIN_UNIT_PRICE, MIN_QUANTITY

logger = logging.getLogger(__name__)


@dataclass
class PreprocessingReport:
    """Structured log of every cleaning step with row counts."""

    raw_rows: int = 0
    after_duplicate_removal: int = 0
    duplicates_removed: int = 0
    missing_customer_id: int = 0
    after_missing_customer_drop: int = 0
    invalid_price_rows: int = 0
    after_price_filter: int = 0
    cancelled_invoices: int = 0  # row count, NOT removed
    data_error_negative_qty: int = 0
    after_negative_qty_filter: int = 0
    final_rows: int = 0
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    unique_customers: int = 0
    unique_invoices: int = 0
    steps: list[str] = field(default_factory=list)

    def add_step(self, msg: str) -> None:
        logger.info(msg)
        self.steps.append(msg)

    def summary_df(self) -> pd.DataFrame:
        rows = [
            ("Raw rows loaded", self.raw_rows, ""),
            ("Duplicate rows removed", self.duplicates_removed, f"→ {self.after_duplicate_removal} remain"),
            ("Rows missing CustomerID", self.missing_customer_id, f"→ {self.after_missing_customer_drop} remain"),
            ("Rows with invalid price (< {:.2f} or 0)".format(MIN_UNIT_PRICE), self.invalid_price_rows, f"→ {self.after_price_filter} remain"),
            ("Cancelled-invoice rows kept (negative revenue)", self.cancelled_invoices, "retained with flag"),
            ("Data-error negative-qty rows removed", self.data_error_negative_qty, f"→ {self.after_negative_qty_filter} remain"),
            ("Final clean rows", self.final_rows, ""),
            ("Date range", "", f"{self.date_range_start} → {self.date_range_end}"),
            ("Unique customers", self.unique_customers, ""),
            ("Unique invoices (all)", self.unique_invoices, ""),
        ]
        return pd.DataFrame(rows, columns=["Step", "Count", "Notes"])


def clean_data(
    df: pd.DataFrame,
    drop_missing_customer: bool = True,
    remove_zero_price: bool = True,
    keep_cancelled: bool = True,
) -> tuple[pd.DataFrame, PreprocessingReport]:
    """
    Clean the raw UCI Online Retail DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Raw data as returned by ``load_data``.
    drop_missing_customer : bool
        If True (default), drop rows where CustomerID is NaN.
    remove_zero_price : bool
        If True (default), drop rows where UnitPrice < MIN_UNIT_PRICE.
    keep_cancelled : bool
        If True (default), retain cancelled invoices flagged by is_cancelled
        so that analysts can compute net-revenue figures.

    Returns
    -------
    (clean_df, report) : tuple
    """
    report = PreprocessingReport()
    df = df.copy()
    report.raw_rows = len(df)
    report.add_step(f"Loaded {report.raw_rows:,} raw rows.")

    # ── 1. Fix data types ────────────────────────────────────────────────────
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["CustomerID"] = pd.to_numeric(df["CustomerID"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["InvoiceNo"] = df["InvoiceNo"].astype(str).str.strip()
    df["StockCode"] = df["StockCode"].astype(str).str.strip()
    df["Description"] = df["Description"].astype(str).str.strip()
    df["Country"] = df["Country"].astype(str).str.strip()

    # ── 2. Flag cancelled invoices BEFORE any row removal ───────────────────
    df["is_cancelled"] = df["InvoiceNo"].str.startswith("C")

    # ── 3. Remove exact duplicates ───────────────────────────────────────────
    before = len(df)
    df.drop_duplicates(inplace=True)
    report.duplicates_removed = before - len(df)
    report.after_duplicate_removal = len(df)
    report.add_step(f"Removed {report.duplicates_removed:,} exact duplicate rows.")

    # ── 4. Handle missing CustomerID ─────────────────────────────────────────
    missing_cid = df["CustomerID"].isna().sum()
    report.missing_customer_id = int(missing_cid)
    if drop_missing_customer:
        df = df[df["CustomerID"].notna()].copy()
        report.after_missing_customer_drop = len(df)
        report.add_step(
            f"Dropped {missing_cid:,} rows with missing CustomerID "
            f"→ {report.after_missing_customer_drop:,} remain."
        )
    else:
        report.after_missing_customer_drop = len(df)
        report.add_step(
            f"Retained {missing_cid:,} rows with missing CustomerID (user choice)."
        )

    df["CustomerID"] = df["CustomerID"].astype(int)

    # ── 5. Remove invalid / zero prices ──────────────────────────────────────
    invalid_price = (df["UnitPrice"].isna()) | (df["UnitPrice"] < MIN_UNIT_PRICE)
    report.invalid_price_rows = int(invalid_price.sum())
    if remove_zero_price:
        df = df[~invalid_price].copy()
    report.after_price_filter = len(df)
    report.add_step(
        f"Removed {report.invalid_price_rows:,} rows with UnitPrice < {MIN_UNIT_PRICE} "
        f"→ {report.after_price_filter:,} remain."
    )

    # ── 6. Handle negative quantities ────────────────────────────────────────
    # Cancelled invoices legitimately have negative quantities.
    # Non-cancelled rows with negative quantity are data errors.
    data_error_mask = (~df["is_cancelled"]) & (df["Quantity"] < MIN_QUANTITY)
    report.data_error_negative_qty = int(data_error_mask.sum())
    df = df[~data_error_mask].copy()
    report.after_negative_qty_filter = len(df)
    report.add_step(
        f"Removed {report.data_error_negative_qty:,} non-cancelled rows with Quantity < {MIN_QUANTITY} "
        f"→ {report.after_negative_qty_filter:,} remain."
    )

    # Cancelled invoice count (retained by default)
    report.cancelled_invoices = int(df["is_cancelled"].sum())
    report.add_step(
        f"Cancelled-invoice rows retained: {report.cancelled_invoices:,} "
        "(flagged as is_cancelled=True; excluded from purchase features)."
    )

    # ── 7. Compute Revenue ───────────────────────────────────────────────────
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]

    # ── 8. Final stats ───────────────────────────────────────────────────────
    report.final_rows = len(df)
    report.date_range_start = str(df["InvoiceDate"].min().date())
    report.date_range_end = str(df["InvoiceDate"].max().date())
    report.unique_customers = df["CustomerID"].nunique()
    report.unique_invoices = df["InvoiceNo"].nunique()
    report.add_step(
        f"Final dataset: {report.final_rows:,} rows | "
        f"{report.unique_customers:,} customers | "
        f"{report.unique_invoices:,} invoices | "
        f"date range {report.date_range_start} → {report.date_range_end}."
    )

    return df, report


def get_purchase_df(clean_df: pd.DataFrame) -> pd.DataFrame:
    """
    Return only valid (non-cancelled) purchase rows.
    Used everywhere that cancelled orders should be excluded.
    """
    return clean_df[~clean_df["is_cancelled"]].copy()
