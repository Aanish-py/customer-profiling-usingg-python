"""
backend/app/api/routes/dataset.py
Dataset ingestion, auditing, filtering, and previewing routes.
"""

import os
import urllib.request
import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
import io
from typing import Optional

from backend.app.core.state import state
from backend.app.core.config import DEFAULT_DATA_FILE, DATA_DIR
from backend.app.schemas.dataset import (
    DatasetStatusResponse,
    AuditReportResponse,
    DataPreviewResponse,
    LoadOptionsRequest,
)
from src.data_loader import load_from_upload

router = APIRouter()


@router.get("/status", response_model=DatasetStatusResponse)
def get_dataset_status():
    file_exists = os.path.exists(DEFAULT_DATA_FILE)
    size_mb = os.path.getsize(DEFAULT_DATA_FILE) / (1024 * 1024) if file_exists else 0.0

    if not state.is_data_loaded:
        return DatasetStatusResponse(
            is_loaded=False,
            file_exists_on_disk=file_exists,
            file_size_mb=round(size_mb, 2),
        )

    clean = state.clean_df
    return DatasetStatusResponse(
        is_loaded=True,
        total_rows=len(clean),
        unique_customers=int(clean["CustomerID"].nunique()),
        unique_invoices=int(clean["InvoiceNo"].nunique()),
        unique_products=int(clean["StockCode"].nunique()),
        date_start=str(clean["InvoiceDate"].min().date()),
        date_end=str(clean["InvoiceDate"].max().date()),
        file_exists_on_disk=file_exists,
        file_size_mb=round(size_mb, 2),
    )


@router.post("/load-disk")
def load_dataset_from_disk(options: LoadOptionsRequest = LoadOptionsRequest()):
    if not os.path.exists(DEFAULT_DATA_FILE):
        raise HTTPException(
            status_code=404,
            detail=f"Dataset file not found at {DEFAULT_DATA_FILE}. Please download it first or upload a file.",
        )
    try:
        report = state.load_dataset_from_file(
            filepath=DEFAULT_DATA_FILE,
            nrows=options.nrows,
            drop_missing_customer=options.drop_missing_customer,
            remove_zero_price=options.remove_zero_price,
            keep_cancelled=options.keep_cancelled,
        )
        return {
            "success": True,
            "message": f"Loaded {report.final_rows:,} rows across {report.unique_customers:,} customers.",
            "report_summary": report.summary_df().to_dict(orient="records"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download-uci")
def download_uci_dataset():
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx"
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, DEFAULT_DATA_FILE)
        size_mb = os.path.getsize(DEFAULT_DATA_FILE) / (1024 * 1024)
        return {"success": True, "size_mb": round(size_mb, 2)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.post("/upload")
async def upload_dataset_file(file: UploadFile = File(...)):
    contents = await file.read()
    bio = io.BytesIO(contents)
    bio.name = file.filename
    try:
        raw_df = load_from_upload(bio)
        report = state.set_uploaded_data(raw_df)
        return {
            "success": True,
            "message": f"Processed {file.filename}: {report.final_rows:,} clean rows.",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")


@router.get("/audit-report", response_model=AuditReportResponse)
def get_audit_report():
    if state.preprocessing_report is None:
        raise HTTPException(status_code=400, detail="No dataset loaded yet.")
    r = state.preprocessing_report
    steps_df = r.summary_df()
    steps = [
        {"step": row["Step"], "count": str(row["Count"]), "notes": str(row["Notes"])}
        for _, row in steps_df.iterrows()
    ]
    return AuditReportResponse(
        steps=steps,
        raw_rows=r.raw_rows,
        duplicates_removed=r.duplicates_removed,
        missing_customer_id=r.missing_customer_id,
        invalid_price_rows=r.invalid_price_rows,
        cancelled_invoices=r.cancelled_invoices,
        final_rows=r.final_rows,
        unique_customers=r.unique_customers,
    )


@router.get("/preview", response_model=DataPreviewResponse)
def get_data_preview(
    kind: str = Query("clean", pattern="^(clean|raw)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=5, le=100),
):
    df = state.clean_df if kind == "clean" else state.raw_df
    if df is None:
        raise HTTPException(status_code=400, detail="No dataset loaded yet.")

    total = len(df)
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total)

    sample = df.iloc[start_idx:end_idx].copy()
    # Serialize datetime and NaN values
    if "InvoiceDate" in sample.columns:
        sample["InvoiceDate"] = sample["InvoiceDate"].astype(str)
    sample = sample.fillna("")

    return DataPreviewResponse(
        columns=list(df.columns),
        total_count=total,
        rows=sample.to_dict(orient="records"),
    )


@router.get("/features", response_model=DataPreviewResponse)
def get_customer_features_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=5, le=100),
    search: Optional[str] = None,
):
    if state.customer_features is None:
        raise HTTPException(status_code=400, detail="Customer features not computed.")

    df = state.customer_features.copy()
    if search:
        search_str = search.strip()
        df = df[df["CustomerID"].astype(str).str.contains(search_str, case=False)]

    total = len(df)
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total)

    sample = df.iloc[start_idx:end_idx].copy()
    for col in ["first_purchase", "last_purchase", "reference_date"]:
        if col in sample.columns:
            sample[col] = sample[col].astype(str)
    sample = sample.fillna(0)

    return DataPreviewResponse(
        columns=list(df.columns),
        total_count=total,
        rows=sample.to_dict(orient="records"),
    )


@router.get("/export-features")
def export_features_csv():
    if state.customer_features is None:
        raise HTTPException(status_code=400, detail="Customer features not computed.")
    csv_bytes = state.customer_features.to_csv(index=False).encode("utf-8")
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=customer_features.csv"},
    )
