"""
backend/app/schemas/dataset.py
Schemas for dataset status, audit reports, and previews.
"""

from pydantic import BaseModel
from typing import Optional, Any


class DatasetStatusResponse(BaseModel):
    is_loaded: bool
    total_rows: int = 0
    unique_customers: int = 0
    unique_invoices: int = 0
    unique_products: int = 0
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    file_exists_on_disk: bool = False
    file_size_mb: float = 0.0


class AuditStep(BaseModel):
    step: str
    count: Any
    notes: str


class AuditReportResponse(BaseModel):
    steps: list[AuditStep]
    raw_rows: int
    duplicates_removed: int
    missing_customer_id: int
    invalid_price_rows: int
    cancelled_invoices: int
    final_rows: int
    unique_customers: int


class DataPreviewResponse(BaseModel):
    columns: list[str]
    total_count: int
    rows: list[dict[str, Any]]


class LoadOptionsRequest(BaseModel):
    nrows: Optional[int] = None
    drop_missing_customer: bool = True
    remove_zero_price: bool = True
    keep_cancelled: bool = True
