"""
backend/app/core/state.py
Singleton application state manager for datasets and trained ML models.
"""

from __future__ import annotations

import logging
import os
import pandas as pd
from typing import Optional, Any

from backend.app.core.config import DEFAULT_DATA_FILE
from src.preprocessing import clean_data, get_purchase_df, PreprocessingReport
from src.feature_engineering import build_customer_features
from src.data_loader import load_data

logger = logging.getLogger("backend.state")


class ApplicationState:
    """Central store for in-memory datasets and trained models."""

    def __init__(self) -> None:
        self.raw_df: Optional[pd.DataFrame] = None
        self.clean_df: Optional[pd.DataFrame] = None
        self.purchase_df: Optional[pd.DataFrame] = None
        self.customer_features: Optional[pd.DataFrame] = None
        self.preprocessing_report: Optional[PreprocessingReport] = None

        # Trained models
        self.segmentation_result: Optional[Any] = None
        self.churn_result: Optional[Any] = None
        self.next_purchase_result: Optional[Any] = None
        self.recommender: Optional[Any] = None
        self.rec_eval: Optional[dict[str, Any]] = None

    @property
    def is_data_loaded(self) -> bool:
        return self.clean_df is not None and self.customer_features is not None

    def clear_models(self) -> None:
        self.segmentation_result = None
        self.churn_result = None
        self.next_purchase_result = None
        self.recommender = None
        self.rec_eval = None

    def load_dataset_from_file(
        self,
        filepath: str = DEFAULT_DATA_FILE,
        nrows: Optional[int] = None,
        drop_missing_customer: bool = True,
        remove_zero_price: bool = True,
        keep_cancelled: bool = True,
    ) -> PreprocessingReport:
        """Load and preprocess the dataset from disk."""
        logger.info("Loading dataset from: %s", filepath)
        raw = load_data(filepath, nrows=nrows)
        clean, report = clean_data(
            raw,
            drop_missing_customer=drop_missing_customer,
            remove_zero_price=remove_zero_price,
            keep_cancelled=keep_cancelled,
        )
        purchases = get_purchase_df(clean)
        features = build_customer_features(purchases)

        self.raw_df = raw
        self.clean_df = clean
        self.purchase_df = purchases
        self.customer_features = features
        self.preprocessing_report = report
        self.clear_models()

        logger.info(
            "Dataset ready: %d rows, %d customers",
            len(clean),
            clean["CustomerID"].nunique(),
        )
        return report

    def set_uploaded_data(
        self,
        raw: pd.DataFrame,
        drop_missing_customer: bool = True,
        remove_zero_price: bool = True,
        keep_cancelled: bool = True,
    ) -> PreprocessingReport:
        clean, report = clean_data(
            raw,
            drop_missing_customer=drop_missing_customer,
            remove_zero_price=remove_zero_price,
            keep_cancelled=keep_cancelled,
        )
        purchases = get_purchase_df(clean)
        features = build_customer_features(purchases)

        self.raw_df = raw
        self.clean_df = clean
        self.purchase_df = purchases
        self.customer_features = features
        self.preprocessing_report = report
        self.clear_models()
        return report


# Global singleton
state = ApplicationState()
