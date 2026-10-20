"""
tests/test_customer_features.py
────────────────────────────────
Tests for customer-level feature engineering and profiling.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_purchase_df() -> pd.DataFrame:
    """Synthetic non-cancelled purchase rows for 3 customers."""
    rows = []
    base = datetime(2011, 1, 1)
    # Customer A: 5 purchases, steady
    for i in range(5):
        rows.append({
            "InvoiceNo": f"INV{i:04d}",
            "StockCode": f"P{i % 3:02d}",
            "Description": f"Product {i % 3}",
            "Quantity": 2,
            "InvoiceDate": base + timedelta(days=i * 30),
            "UnitPrice": 10.0,
            "Revenue": 20.0,
            "CustomerID": 1001,
            "Country": "United Kingdom",
            "is_cancelled": False,
        })
    # Customer B: 1 purchase only
    rows.append({
        "InvoiceNo": "INV9001",
        "StockCode": "P01",
        "Description": "Product 1",
        "Quantity": 5,
        "InvoiceDate": base + timedelta(days=10),
        "UnitPrice": 25.0,
        "Revenue": 125.0,
        "CustomerID": 1002,
        "Country": "Germany",
        "is_cancelled": False,
    })
    # Customer C: 3 purchases
    for i in range(3):
        rows.append({
            "InvoiceNo": f"INV{9100+i:04d}",
            "StockCode": f"P{i:02d}",
            "Description": f"Product {i}",
            "Quantity": 1,
            "InvoiceDate": base + timedelta(days=i * 14),
            "UnitPrice": 5.0,
            "Revenue": 5.0,
            "CustomerID": 1003,
            "Country": "France",
            "is_cancelled": False,
        })
    return pd.DataFrame(rows)


class TestBuildCustomerFeatures:
    def setup_method(self):
        self.purchase_df = _make_purchase_df()

    def test_one_row_per_customer(self):
        from src.feature_engineering import build_customer_features
        cf = build_customer_features(self.purchase_df)
        assert len(cf) == 3
        assert cf["CustomerID"].nunique() == 3

    def test_recency_non_negative(self):
        from src.feature_engineering import build_customer_features
        cf = build_customer_features(self.purchase_df)
        assert (cf["recency"] >= 0).all()

    def test_frequency_correct(self):
        from src.feature_engineering import build_customer_features
        cf = build_customer_features(self.purchase_df)
        a = cf[cf["CustomerID"] == 1001]["frequency"].iloc[0]
        b = cf[cf["CustomerID"] == 1002]["frequency"].iloc[0]
        c = cf[cf["CustomerID"] == 1003]["frequency"].iloc[0]
        assert a == 5
        assert b == 1
        assert c == 3

    def test_monetary_positive(self):
        from src.feature_engineering import build_customer_features
        cf = build_customer_features(self.purchase_df)
        assert (cf["monetary"] > 0).all()

    def test_monetary_customer_a(self):
        from src.feature_engineering import build_customer_features
        cf = build_customer_features(self.purchase_df)
        a = cf[cf["CustomerID"] == 1001]["monetary"].iloc[0]
        assert abs(a - 100.0) < 1e-6   # 5 purchases × £20

    def test_repeat_rate_one_purchase(self):
        from src.feature_engineering import build_customer_features
        cf = build_customer_features(self.purchase_df)
        b = cf[cf["CustomerID"] == 1002]["repeat_rate"].iloc[0]
        assert b == 0

    def test_repeat_rate_multi_purchase(self):
        from src.feature_engineering import build_customer_features
        cf = build_customer_features(self.purchase_df)
        a = cf[cf["CustomerID"] == 1001]["repeat_rate"].iloc[0]
        assert a == 1

    def test_unique_products(self):
        from src.feature_engineering import build_customer_features
        cf = build_customer_features(self.purchase_df)
        a = cf[cf["CustomerID"] == 1001]["unique_products"].iloc[0]
        assert a == 3   # P00, P01, P02

    def test_tenure_zero_for_single_purchase(self):
        from src.feature_engineering import build_customer_features
        cf = build_customer_features(self.purchase_df)
        b = cf[cf["CustomerID"] == 1002]["tenure_days"].iloc[0]
        assert b == 0

    def test_tenure_positive_for_multi_purchase(self):
        from src.feature_engineering import build_customer_features
        cf = build_customer_features(self.purchase_df)
        a = cf[cf["CustomerID"] == 1001]["tenure_days"].iloc[0]
        assert a > 0

    def test_reference_date_override(self):
        from src.feature_engineering import build_customer_features
        ref = datetime(2011, 12, 31)
        cf = build_customer_features(self.purchase_df, reference_date=pd.Timestamp(ref))
        # All recency values should be positive (last purchase before reference)
        assert (cf["recency"] >= 0).all()


class TestGetCustomerProfile:
    def setup_method(self):
        from src.feature_engineering import build_customer_features
        from src.preprocessing import clean_data
        # Inject is_cancelled column for clean_df compatibility
        self.purchase_df = _make_purchase_df()
        self.cf = build_customer_features(self.purchase_df)
        self.clean_df = self.purchase_df.copy()

    def test_profile_returns_dict(self):
        from src.customer_profiling import get_customer_profile
        profile = get_customer_profile(1001, self.cf, self.clean_df)
        assert isinstance(profile, dict)
        assert "metrics" in profile

    def test_unknown_customer_returns_empty(self):
        from src.customer_profiling import get_customer_profile
        profile = get_customer_profile(9999, self.cf, self.clean_df)
        assert profile == {}

    def test_top_products_non_empty(self):
        from src.customer_profiling import _top_products
        cust_df = self.purchase_df[self.purchase_df["CustomerID"] == 1001]
        top = _top_products(cust_df)
        assert len(top) > 0
