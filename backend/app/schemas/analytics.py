"""
backend/app/schemas/analytics.py
Schemas for executive KPIs, macro charts, and distributions.
"""

from pydantic import BaseModel
from typing import Any, Optional


class KPIResponse(BaseModel):
    total_revenue: float
    unique_customers: int
    total_orders: int
    avg_order_value: float
    cancellation_rate: float
    unique_products: int
    date_start: str
    date_end: str


class MonthlyPoint(BaseModel):
    month: str
    revenue: float
    orders: int


class CategoryPoint(BaseModel):
    name: str
    value: float
    percentage: Optional[float] = None


class OverviewChartsResponse(BaseModel):
    monthly_trend: list[MonthlyPoint]
    repeat_vs_onetime: list[CategoryPoint]
    country_revenue: list[CategoryPoint]


class DistributionBin(BaseModel):
    bin: str
    count: int


class DistributionsResponse(BaseModel):
    price_distribution: list[DistributionBin]
    quantity_distribution: list[DistributionBin]
    revenue_distribution: list[DistributionBin]
