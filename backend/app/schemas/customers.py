"""
backend/app/schemas/customers.py
Schemas for customer 360 profiles and searches.
"""

from pydantic import BaseModel
from typing import Any, Optional


class CustomerSearchItem(BaseModel):
    customer_id: int
    frequency: int
    monetary: float
    recency: int
    country: str


class CustomerOrderItem(BaseModel):
    invoice_no: str
    date: str
    items_count: int
    total_revenue: float


class CustomerTopProduct(BaseModel):
    stock_code: str
    description: str
    total_qty: int
    total_spend: float
    order_count: int


class CustomerPredictionBadges(BaseModel):
    segment_name: Optional[str] = None
    churn_probability: Optional[float] = None
    churn_risk_level: Optional[str] = None
    next_purchase_days: Optional[float] = None
    next_purchase_date: Optional[str] = None
    recommended_products: list[dict[str, Any]] = []


class CustomerProfileResponse(BaseModel):
    customer_id: int
    country: str
    first_purchase: str
    last_purchase: str
    frequency: int
    monetary: float
    avg_order_value: float
    avg_qty_per_order: float
    recency: int
    tenure_days: int
    repeat_rate: int
    unique_products: int
    inter_order_days: Optional[float] = None
    order_history: list[CustomerOrderItem]
    top_products: list[CustomerTopProduct]
    predictions: CustomerPredictionBadges
