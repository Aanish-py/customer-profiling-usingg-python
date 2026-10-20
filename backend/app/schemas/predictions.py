"""
backend/app/schemas/predictions.py
Schemas for next-purchase regression and churn classification models.
"""

from pydantic import BaseModel
from typing import Any, Optional


# ── Next Purchase Schemas ──
class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float


class NextPurchaseMetricsResponse(BaseModel):
    is_trained: bool
    best_model_name: str
    model_mae: float
    model_rmse: float
    model_r2: float
    baseline_mae: float
    mae_improvement_pct: float
    sample_count: int
    feature_importances: list[FeatureImportanceItem]
    notes: list[str]


class NextPurchaseEstimateRequest(BaseModel):
    customer_id: int


class NextPurchaseEstimateResponse(BaseModel):
    customer_id: int
    predicted_days: float
    predicted_date: str
    model_used: str
    confidence_note: str


class BatchNextPurchaseItem(BaseModel):
    customer_id: int
    last_purchase_date: str
    predicted_days: float
    predicted_next_date: str
    status: str  # "Overdue", "Due Soon", "On Track"


# ── Churn Prediction Schemas ──
class ROCCurvePoint(BaseModel):
    fpr: float
    tpr: float


class ConfusionMatrixData(BaseModel):
    tn: int
    fp: int
    fn: int
    tp: int
    threshold: float


class ChurnMetricsResponse(BaseModel):
    is_trained: bool
    best_model_name: str
    churn_rate: float
    lr_auc: float
    rf_auc: float
    best_auc: float
    baseline_auc: float = 0.50
    precision: float
    recall: float
    f1: float
    train_size: int
    test_size: int
    roc_curve: list[ROCCurvePoint]
    confusion_matrix: ConfusionMatrixData
    feature_importances: list[FeatureImportanceItem]
    notes: list[str]


class AtRiskCustomerItem(BaseModel):
    customer_id: int
    churn_probability: float
    risk_level: str  # "High", "Medium", "Low"
    recency_days: int
    frequency: int
    monetary: float
    country: str


class TrainChurnRequest(BaseModel):
    churn_window_days: int = 90
