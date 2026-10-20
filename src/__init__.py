"""
src/__init__.py
Makes `src` a Python package and re-exports the most commonly used helpers
so that page scripts can do ``from src import load_data, clean_data`` etc.
"""

from src.data_loader import load_data, validate_columns
from src.preprocessing import clean_data, PreprocessingReport
from src.feature_engineering import build_customer_features
from src.customer_profiling import get_customer_profile, get_customer_orders
from src.segmentation import train_segmentation, assign_segments
from src.next_purchase import train_next_purchase_model, predict_next_purchase
from src.churn_prediction import train_churn_model, predict_churn
from src.recommendations import build_recommender, get_recommendations
from src.evaluation import evaluate_classifier, evaluate_regressor

__all__ = [
    "load_data",
    "validate_columns",
    "clean_data",
    "PreprocessingReport",
    "build_customer_features",
    "get_customer_profile",
    "get_customer_orders",
    "train_segmentation",
    "assign_segments",
    "train_next_purchase_model",
    "predict_next_purchase",
    "train_churn_model",
    "predict_churn",
    "build_recommender",
    "get_recommendations",
    "evaluate_classifier",
    "evaluate_regressor",
]
