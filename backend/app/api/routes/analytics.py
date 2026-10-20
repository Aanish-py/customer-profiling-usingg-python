"""
backend/app/api/routes/analytics.py
Executive dashboard analytics and distribution routes.
"""

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

from backend.app.core.state import state
from backend.app.schemas.analytics import (
    KPIResponse,
    OverviewChartsResponse,
    MonthlyPoint,
    CategoryPoint,
    DistributionsResponse,
    DistributionBin,
)

router = APIRouter()


@router.get("/kpis", response_model=KPIResponse)
def get_executive_kpis():
    if not state.is_data_loaded:
        raise HTTPException(status_code=400, detail="Dataset not loaded.")

    clean_df = state.clean_df
    purchase_df = state.purchase_df

    total_revenue = float(purchase_df["Revenue"].sum())
    unique_customers = int(purchase_df["CustomerID"].nunique())
    total_orders = int(purchase_df["InvoiceNo"].nunique())
    avg_order_value = float(purchase_df.groupby("InvoiceNo")["Revenue"].sum().mean())
    cancellation_rate = float(clean_df["is_cancelled"].mean() * 100)
    unique_products = int(purchase_df["StockCode"].nunique())

    return KPIResponse(
        total_revenue=round(total_revenue, 2),
        unique_customers=unique_customers,
        total_orders=total_orders,
        avg_order_value=round(avg_order_value, 2),
        cancellation_rate=round(cancellation_rate, 2),
        unique_products=unique_products,
        date_start=str(purchase_df["InvoiceDate"].min().date()),
        date_end=str(purchase_df["InvoiceDate"].max().date()),
    )


@router.get("/overview-charts", response_model=OverviewChartsResponse)
def get_overview_charts():
    if not state.is_data_loaded:
        raise HTTPException(status_code=400, detail="Dataset not loaded.")

    purchase_df = state.purchase_df
    cust_feat = state.customer_features

    # Monthly revenue & orders trend
    df = purchase_df.copy()
    df["YearMonth"] = df["InvoiceDate"].dt.to_period("M").astype(str)
    monthly = (
        df.groupby("YearMonth")
        .agg(revenue=("Revenue", "sum"), orders=("InvoiceNo", "nunique"))
        .reset_index()
    )
    monthly_trend = [
        MonthlyPoint(
            month=row["YearMonth"],
            revenue=round(float(row["revenue"]), 2),
            orders=int(row["orders"]),
        )
        for _, row in monthly.iterrows()
    ]

    # Repeat vs One-time buyers
    one_time = int((cust_feat["frequency"] == 1).sum())
    repeat = int((cust_feat["frequency"] > 1).sum())
    total_cust = one_time + repeat
    repeat_vs_onetime = [
        CategoryPoint(
            name="Repeat Buyers (>1 order)",
            value=repeat,
            percentage=round(repeat / total_cust * 100, 1) if total_cust else 0.0,
        ),
        CategoryPoint(
            name="One-Time Buyers (1 order)",
            value=one_time,
            percentage=round(one_time / total_cust * 100, 1) if total_cust else 0.0,
        ),
    ]

    # Top countries by revenue
    country_agg = (
        purchase_df.groupby("Country")["Revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    tot_rev = purchase_df["Revenue"].sum()
    country_revenue = [
        CategoryPoint(
            name=row["Country"],
            value=round(float(row["Revenue"]), 2),
            percentage=round(float(row["Revenue"]) / tot_rev * 100, 1) if tot_rev else 0.0,
        )
        for _, row in country_agg.iterrows()
    ]

    return OverviewChartsResponse(
        monthly_trend=monthly_trend,
        repeat_vs_onetime=repeat_vs_onetime,
        country_revenue=country_revenue,
    )


@router.get("/distributions", response_model=DistributionsResponse)
def get_distributions():
    if not state.is_data_loaded:
        raise HTTPException(status_code=400, detail="Dataset not loaded.")

    purchase_df = state.purchase_df

    def make_bins(series, bins_count=10, max_val=None):
        vals = series.dropna()
        if max_val:
            vals = vals[vals <= max_val]
        counts, edges = np.histogram(vals, bins=bins_count)
        return [
            DistributionBin(
                bin=f"£{edges[i]:.0f}–£{edges[i+1]:.0f}" if "price" in str(series.name).lower() or "rev" in str(series.name).lower() else f"{int(edges[i])}–{int(edges[i+1])}",
                count=int(counts[i]),
            )
            for i in range(len(counts))
        ]

    price_bins = make_bins(purchase_df["UnitPrice"], bins_count=8, max_val=20.0)
    qty_bins = make_bins(purchase_df["Quantity"], bins_count=8, max_val=100.0)
    order_rev = purchase_df.groupby("InvoiceNo")["Revenue"].sum()
    order_rev.name = "Revenue"
    rev_bins = make_bins(order_rev, bins_count=8, max_val=1000.0)

    return DistributionsResponse(
        price_distribution=price_bins,
        quantity_distribution=qty_bins,
        revenue_distribution=rev_bins,
    )
