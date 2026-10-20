"""
backend/app/schemas/recommendations.py
Schemas for product recommendations and association rules.
"""

from pydantic import BaseModel
from typing import Any, Optional


class ProductRecommendation(BaseModel):
    stock_code: str
    description: str
    score: float
    reason: str


class AssociationRuleItem(BaseModel):
    antecedents: list[str]
    consequents: list[str]
    support: float
    confidence: float
    lift: float


class PopularProductItem(BaseModel):
    stock_code: str
    description: str
    total_qty: int
    order_count: int


class RecommendationEvaluationResponse(BaseModel):
    is_built: bool
    hit_rate_at_n: float
    mrr_at_n: float
    catalog_size: int
    test_customers_evaluated: int
    top_n: int


class CustomerRecommendationsResponse(BaseModel):
    customer_id: int
    recommendations: list[ProductRecommendation]


class BuildRecommenderRequest(BaseModel):
    top_n: int = 10
