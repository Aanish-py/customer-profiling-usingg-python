"""
backend/app/api/routes/customers.py
Customer 360 profile and search routes.
"""

from datetime import timedelta
import math
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from backend.app.core.state import state
from backend.app.schemas.customers import (
    CustomerSearchItem,
    CustomerProfileResponse,
    CustomerOrderItem,
    CustomerTopProduct,
    CustomerPredictionBadges,
)
from src.customer_profiling import get_customer_profile
from src.churn_prediction import predict_churn
from src.next_purchase import predict_next_purchase
from src.recommendations import get_recommendations

router = APIRouter()


@router.get("/search", response_model=list[CustomerSearchItem])
def search_customers(
    q: str = Query("", description="Query string for customer ID"),
    limit: int = Query(20, ge=1, le=100),
):
    if state.customer_features is None:
        raise HTTPException(status_code=400, detail="Dataset not loaded.")

    df = state.customer_features
    if q.strip():
        mask = df["CustomerID"].astype(str).str.contains(q.strip(), case=False)
        matched = df[mask]
    else:
        matched = df.sort_values("monetary", ascending=False)

    sample = matched.head(limit)
    return [
        CustomerSearchItem(
            customer_id=int(row["CustomerID"]),
            frequency=int(row["frequency"]),
            monetary=round(float(row["monetary"]), 2),
            recency=int(row["recency"]),
            country=str(row["country"]),
        )
        for _, row in sample.iterrows()
    ]


@router.get("/{customer_id}/profile", response_model=CustomerProfileResponse)
def get_customer_profile_data(customer_id: int):
    if not state.is_data_loaded:
        raise HTTPException(status_code=400, detail="Dataset not loaded.")

    raw_profile = get_customer_profile(
        customer_id=customer_id,
        purchase_df=state.purchase_df,
        customer_features=state.customer_features,
    )
    if not raw_profile:
        raise HTTPException(status_code=404, detail=f"Customer ID {customer_id} not found.")

    # Order history
    inv_df = (
        state.purchase_df[state.purchase_df["CustomerID"] == customer_id]
        .groupby("InvoiceNo")
        .agg(
            date=("InvoiceDate", "max"),
            items_count=("Quantity", "sum"),
            total_revenue=("Revenue", "sum"),
        )
        .sort_values("date", ascending=False)
        .reset_index()
    )
    order_history = [
        CustomerOrderItem(
            invoice_no=row["InvoiceNo"],
            date=str(row["date"].date()),
            items_count=int(row["items_count"]),
            total_revenue=round(float(row["total_revenue"]), 2),
        )
        for _, row in inv_df.iterrows()
    ]

    # Top products
    top_p = raw_profile.get("top_products", pd.DataFrame())
    top_products = []
    if isinstance(top_p, pd.DataFrame) and not top_p.empty:
        top_products = [
            CustomerTopProduct(
                stock_code=str(row["StockCode"]),
                description=str(row["Description"]),
                total_qty=int(row["TotalQty"]),
                total_spend=round(float(row["TotalSpend"]), 2),
                order_count=int(row["Invoices"]),
            )
            for _, row in top_p.iterrows()
        ]

    # Model predictions if trained
    badges = CustomerPredictionBadges()

    # 1. Segment badge
    if state.segmentation_result is not None:
        seg_res = state.segmentation_result
        if hasattr(seg_res, "labeled_features") and customer_id in seg_res.labeled_features["CustomerID"].values:
            row = seg_res.labeled_features[seg_res.labeled_features["CustomerID"] == customer_id].iloc[0]
            badges.segment_name = str(row.get("segment_name", f"Cluster {row.get('cluster')}"))

    # 2. Churn probability
    if state.churn_result is not None and state.churn_result.best_pipeline is not None:
        prob = predict_churn(
            customer_id=customer_id,
            purchase_df=state.purchase_df,
            result=state.churn_result,
        )
        if prob is not None and not math.isnan(prob):
            badges.churn_probability = round(prob, 3)
            badges.churn_risk_level = "High" if prob >= 0.7 else "Medium" if prob >= 0.4 else "Low"

    # 3. Next purchase days
    if state.next_purchase_result is not None and state.next_purchase_result.best_pipeline is not None:
        pred_days = predict_next_purchase(
            customer_id=customer_id,
            purchase_df=state.purchase_df,
            result=state.next_purchase_result,
        )
        if pred_days is not None and not math.isnan(pred_days):
            badges.next_purchase_days = round(pred_days, 1)
            last_date = pd.to_datetime(raw_profile["last_purchase"])
            est_date = last_date + timedelta(days=float(pred_days))
            badges.next_purchase_date = str(est_date.date())

    # 4. Recommendations
    if state.recommender is not None:
        recs = get_recommendations(state.recommender, customer_id=customer_id, top_n=5)
        badges.recommended_products = [
            {
                "stock_code": r.stock_code,
                "description": r.description,
                "score": round(r.score, 3),
                "reason": r.reason,
            }
            for r in recs
        ]

    inter_order = raw_profile.get("inter_order_days")
    if pd.isna(inter_order):
        inter_order = None
    else:
        inter_order = round(float(inter_order), 1)

    return CustomerProfileResponse(
        customer_id=int(raw_profile["CustomerID"]),
        country=str(raw_profile["country"]),
        first_purchase=str(raw_profile["first_purchase"].date()),
        last_purchase=str(raw_profile["last_purchase"].date()),
        frequency=int(raw_profile["frequency"]),
        monetary=round(float(raw_profile["monetary"]), 2),
        avg_order_value=round(float(raw_profile["avg_order_value"]), 2),
        avg_qty_per_order=round(float(raw_profile["avg_qty_per_order"]), 2),
        recency=int(raw_profile["recency"]),
        tenure_days=int(raw_profile["tenure_days"]),
        repeat_rate=int(raw_profile["repeat_rate"]),
        unique_products=int(raw_profile["unique_products"]),
        inter_order_days=inter_order,
        order_history=order_history,
        top_products=top_products,
        predictions=badges,
    )
