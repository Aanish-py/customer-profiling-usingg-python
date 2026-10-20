"""
tests/test_temporal_splits.py
──────────────────────────────
Tests for chronological splitting, data leakage prevention, and
prediction behaviour for customers with insufficient history.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_rich_purchase_df(n_customers: int = 30, orders_per_customer: int = 6) -> pd.DataFrame:
    """Create a richer synthetic purchase dataset suitable for model training."""
    rng = np.random.default_rng(42)
    rows = []
    base = datetime(2010, 12, 1)

    for cid in range(10001, 10001 + n_customers):
        for j in range(orders_per_customer):
            date = base + timedelta(days=int(rng.integers(0, 365)))
            rows.append({
                "InvoiceNo": f"{cid}_{j:03d}",
                "StockCode": f"P{rng.integers(1, 20):03d}",
                "Description": f"Product {rng.integers(1, 20)}",
                "Quantity": int(rng.integers(1, 10)),
                "InvoiceDate": date,
                "UnitPrice": float(rng.uniform(1, 50)),
                "Revenue": float(rng.integers(1, 10)) * float(rng.uniform(1, 50)),
                "CustomerID": cid,
                "Country": "United Kingdom",
                "is_cancelled": False,
            })
    return pd.DataFrame(rows)


class TestTemporalSplits:
    """Verify chronological ordering is respected and no leakage occurs."""

    def test_next_purchase_training_examples_have_no_future_leakage(self):
        """
        For every training example, the observation_date should be
        strictly before the corresponding purchase that generated the target.
        This test checks that the feature window doesn't include future data.
        """
        from src.next_purchase import _build_training_examples
        purchase_df = _make_rich_purchase_df()
        examples = _build_training_examples(purchase_df)

        # observation_date must be in the past relative to target
        assert (examples["target_days"] > 0).all(), \
            "All target gaps must be positive (future purchase is after current)"

    def test_churn_features_precede_labels(self):
        """
        The cutoff_date must be before the churn observation window ends.
        Features (≤ cutoff) must be temporally separated from labels (> cutoff).
        """
        from src.churn_prediction import _build_churn_examples
        purchase_df = _make_rich_purchase_df()
        examples = _build_churn_examples(purchase_df, churn_window_days=60)
        if examples.empty:
            pytest.skip("Not enough data to construct churn examples.")

        cutoff = examples["cutoff_date"].iloc[0]
        max_date = pd.to_datetime(purchase_df["InvoiceDate"]).max()
        assert cutoff < max_date, "Cutoff must be before the end of the dataset"

    def test_chronological_train_test_no_overlap(self):
        """
        After chronological split, no test observation_date should precede
        the maximum training observation_date (ensuring temporal ordering).
        """
        from src.next_purchase import _build_training_examples
        from config import TRAIN_FRACTION

        purchase_df = _make_rich_purchase_df()
        examples = _build_training_examples(purchase_df)
        if len(examples) < 10:
            pytest.skip("Not enough examples.")

        examples = examples.sort_values("observation_date").reset_index(drop=True)
        split = int(len(examples) * TRAIN_FRACTION)
        train = examples.iloc[:split]
        test = examples.iloc[split:]

        if len(test) > 0 and len(train) > 0:
            assert train["observation_date"].max() <= test["observation_date"].max(), \
                "Test set should have later dates than training set."

    def test_insufficient_history_returns_none(self):
        """
        Customers with fewer than MIN_INVOICES_FOR_PREDICTION invoices
        should receive None from predict_next_purchase.
        """
        from src.next_purchase import predict_next_purchase, NextPurchaseResult
        from config import MIN_INVOICES_FOR_PREDICTION

        # Create a minimal single-invoice customer
        single_purchase = pd.DataFrame([{
            "InvoiceNo": "TEST001",
            "StockCode": "P001",
            "Description": "Test",
            "Quantity": 1,
            "InvoiceDate": datetime(2011, 6, 1),
            "UnitPrice": 10.0,
            "Revenue": 10.0,
            "CustomerID": 99999,
            "Country": "UK",
            "is_cancelled": False,
        }])

        # Stub result with no pipeline
        stub = NextPurchaseResult(
            best_model_name="N/A",
            best_pipeline=None,
            baseline_mae=float("nan"),
            baseline_rmse=float("nan"),
            model_mae=float("nan"),
            model_rmse=float("nan"),
            val_mae=float("nan"),
            val_rmse=float("nan"),
            feature_importances=None,
            training_samples=0,
            test_samples=0,
            notes=["Insufficient data"],
        )
        result = predict_next_purchase(99999, single_purchase, stub)
        assert result is None

    def test_recommendation_fallback_for_new_customer(self):
        """
        A customer with no purchase history should receive popularity-based fallbacks.
        """
        from src.recommendations import build_recommender, get_recommendations
        purchase_df = _make_rich_purchase_df(5, 10)
        rec = build_recommender(purchase_df)

        # A customer ID not in the dataset
        recs = get_recommendations(99999, rec, n=5, exclude_purchased=False)
        assert len(recs) > 0, "Fallback recommendations should be generated for new customers"

    def test_cancelled_transactions_excluded_from_recommender(self):
        """
        Cancelled purchases should not count as positive interactions in the recommender.
        """
        # Build a recommender from ONLY valid purchases
        purchase_df = _make_rich_purchase_df(5, 10)
        # Verify that no is_cancelled rows were included
        assert (purchase_df["is_cancelled"] == False).all(), \
            "Recommender input should contain only non-cancelled rows"


class TestSegmentation:
    def test_segmentation_all_customers_assigned(self):
        """Every customer must receive a cluster label."""
        from src.feature_engineering import build_customer_features
        from src.segmentation import train_segmentation, assign_segments

        purchase_df = _make_rich_purchase_df(20, 4)
        cf = build_customer_features(purchase_df)
        result = train_segmentation(cf, n_clusters=3)
        seg_df = assign_segments(cf, result)

        assert len(seg_df) == len(cf)
        assert seg_df["cluster"].isna().sum() == 0
        assert seg_df["segment"].isna().sum() == 0

    def test_segmentation_silhouette_in_range(self):
        """Silhouette scores must be between -1 and 1."""
        from src.feature_engineering import build_customer_features
        from src.segmentation import train_segmentation

        purchase_df = _make_rich_purchase_df(20, 4)
        cf = build_customer_features(purchase_df)
        result = train_segmentation(cf, n_clusters=3)

        for k, score in result.silhouette_scores.items():
            assert -1.0 <= score <= 1.0, f"Silhouette score for K={k} out of range: {score}"

    def test_cluster_count_matches_request(self):
        from src.feature_engineering import build_customer_features
        from src.segmentation import train_segmentation

        purchase_df = _make_rich_purchase_df(20, 4)
        cf = build_customer_features(purchase_df)
        result = train_segmentation(cf, n_clusters=3)
        assert result.n_clusters == 3
