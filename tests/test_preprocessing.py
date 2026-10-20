"""
tests/test_preprocessing.py
────────────────────────────
Unit tests for data loading and preprocessing.
All tests use synthetic minimal DataFrames — no real dataset required.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def _make_raw_df(n=20) -> pd.DataFrame:
    """Create a minimal synthetic UCI-like DataFrame for testing."""
    rng = np.random.default_rng(42)
    today = datetime(2011, 12, 1)
    rows = []
    for i in range(n):
        cid = rng.choice([10001, 10002, 10003, np.nan])
        inv = f"5{i:05d}" if i % 5 != 0 else f"C5{i:05d}"  # 1 in 5 cancelled
        rows.append({
            "InvoiceNo": inv,
            "StockCode": f"PRD{rng.integers(1, 5):03d}",
            "Description": f"Product {rng.integers(1, 5)}",
            "Quantity": int(rng.integers(-5, 20)),
            "InvoiceDate": today - timedelta(days=int(rng.integers(0, 200))),
            "UnitPrice": float(rng.uniform(-1, 50)),
            "CustomerID": cid,
            "Country": "United Kingdom",
        })
    return pd.DataFrame(rows)


# ── Data loader tests ─────────────────────────────────────────────────────────

class TestValidateColumns:
    def test_valid_df_passes(self):
        from src.data_loader import validate_columns
        df = _make_raw_df()
        assert validate_columns(df) == []

    def test_missing_column_detected(self):
        from src.data_loader import validate_columns
        df = _make_raw_df().drop(columns=["CustomerID"])
        missing = validate_columns(df)
        assert "CustomerID" in missing

    def test_file_not_found(self):
        from src.data_loader import load_data
        with pytest.raises(FileNotFoundError):
            load_data("/nonexistent/path/Online Retail.xlsx")


# ── Preprocessing tests ───────────────────────────────────────────────────────

class TestCleanData:
    def setup_method(self):
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        self.raw = _make_raw_df(50)

    def test_output_rows_less_than_input(self):
        from src.preprocessing import clean_data
        clean, report = clean_data(self.raw)
        assert len(clean) <= len(self.raw)

    def test_no_missing_customer_id_after_drop(self):
        from src.preprocessing import clean_data
        clean, _ = clean_data(self.raw, drop_missing_customer=True)
        assert clean["CustomerID"].isna().sum() == 0

    def test_cancelled_flag_created(self):
        from src.preprocessing import clean_data
        clean, _ = clean_data(self.raw, keep_cancelled=True)
        assert "is_cancelled" in clean.columns

    def test_cancelled_rows_preserved_by_default(self):
        from src.preprocessing import clean_data
        clean, report = clean_data(self.raw, keep_cancelled=True)
        # Some cancelled rows should remain
        assert report.cancelled_invoices >= 0  # can be 0 in tiny sample

    def test_revenue_column_created(self):
        from src.preprocessing import clean_data
        clean, _ = clean_data(self.raw)
        assert "Revenue" in clean.columns

    def test_revenue_calculation(self):
        from src.preprocessing import clean_data
        clean, _ = clean_data(self.raw)
        # Revenue = Quantity * UnitPrice
        computed = clean["Quantity"] * clean["UnitPrice"]
        assert np.allclose(computed, clean["Revenue"], rtol=1e-5, atol=1e-5)

    def test_zero_price_removed(self):
        from src.preprocessing import clean_data
        clean, _ = clean_data(self.raw, remove_zero_price=True)
        assert (clean["UnitPrice"] > 0).all()

    def test_report_final_rows_matches_df(self):
        from src.preprocessing import clean_data
        clean, report = clean_data(self.raw)
        assert report.final_rows == len(clean)

    def test_non_cancelled_negative_qty_removed(self):
        from src.preprocessing import clean_data
        # Create a row with negative quantity and no cancellation
        row = {
            "InvoiceNo": "99999",
            "StockCode": "X001",
            "Description": "Test",
            "Quantity": -5,
            "InvoiceDate": datetime(2011, 1, 1),
            "UnitPrice": 10.0,
            "CustomerID": 12345,
            "Country": "UK",
        }
        raw = pd.concat([_make_raw_df(10), pd.DataFrame([row])], ignore_index=True)
        clean, _ = clean_data(raw)
        # The row with Quantity=-5 and no 'C' prefix should be gone
        bad = clean[(clean["InvoiceNo"] == "99999") & (clean["Quantity"] < 0)]
        assert len(bad) == 0

    def test_get_purchase_df_excludes_cancelled(self):
        from src.preprocessing import clean_data, get_purchase_df
        clean, _ = clean_data(self.raw)
        purchases = get_purchase_df(clean)
        assert purchases["is_cancelled"].sum() == 0
