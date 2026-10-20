"""
backend/app/schemas/segmentation.py
Schemas for K-Means customer segmentation.
"""

from pydantic import BaseModel
from typing import Any, Optional


class CurvePoint(BaseModel):
    k: int
    score: float


class SegmentationCurvesResponse(BaseModel):
    elbow_curve: list[CurvePoint]
    silhouette_curve: list[CurvePoint]
    recommended_k: int


class ClusterProfileItem(BaseModel):
    cluster: int
    name: str
    count: int
    pct_customers: float
    mean_recency: float
    mean_frequency: float
    mean_monetary: float
    mean_aov: float
    description: str


class PCAPoint(BaseModel):
    customer_id: int
    pca1: float
    pca2: float
    cluster: int
    cluster_name: str
    monetary: float
    frequency: int
    recency: int


class SegmentationResultResponse(BaseModel):
    n_clusters: int
    silhouette_score: float
    profiles: list[ClusterProfileItem]
    pca_points: list[PCAPoint]


class TrainSegmentationRequest(BaseModel):
    n_clusters: Optional[int] = None  # None or 0 = auto-select
