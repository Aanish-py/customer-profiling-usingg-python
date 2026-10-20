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
        clean_df=state.clean_df,
        customer_features=state.customer_features,
    )
    if not raw_profile or "metrics" not in raw_profile:
        raise HTTPException(status_code=404, detail=f"Customer ID {customer_id} not found.")

    metrics = raw_profile["metrics"]

    # Order history from raw_profile orders DataFrame
    orders_df = raw_profile.get("orders", pd.DataFrame())
    order_history = []
    if isinstance(orders_df, pd.DataFrame) and not orders_df.empty:
        for _, row in orders_df.iterrows():
            inv_date = row["InvoiceDate"]
            date_str = str(inv_date.date()) if hasattr(inv_date, "date") else str(inv_date)
            order_history.append(
                CustomerOrderItem(
                    invoice_no=str(row["InvoiceNo"]),
                    date=date_str,
                    items_count=int(row["Items"]),
                    total_revenue=round(float(row["Revenue"]), 2),
                )
            )

    # Top products from raw_profile top_products DataFrame
    top_p = raw_profile.get("top_products", pd.DataFrame())
    top_products = []
    if isinstance(top_p, pd.DataFrame) and not top_p.empty:
        for _, row in top_p.iterrows():
            top_products.append(
                CustomerTopProduct(
                    stock_code=str(row["StockCode"]),
                    description=str(row.get("Description", row["StockCode"])),
                    total_qty=int(row.get("Quantity", 0)),
                    total_spend=round(float(row.get("Revenue", 0.0)), 2),
                    order_count=1,
                )
            )

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
            last_date = pd.to_datetime(metrics["last_purchase"])
            est_date = last_date + timedelta(days=float(pred_days))
            badges.next_purchase_date = str(est_date.date())

    # 4. Recommendations
    if state.recommender is not None:
        rec_df = get_recommendations(
            customer_id=customer_id,
            recommender=state.recommender,
            n=5,
        )
        if isinstance(rec_df, pd.DataFrame) and not rec_df.empty:
            badges.recommended_products = [
                {
                    "stock_code": str(r["StockCode"]),
                    "description": str(r.get("Description", r["StockCode"])),
                    "score": round(float(r.get("score", 0.0)), 3),
                    "reason": str(r.get("reason", "")),
                }
                for _, r in rec_df.iterrows()
            ]

    inter_order = metrics.get("inter_order_days")
    if pd.isna(inter_order):
        inter_order = None
    else:
        inter_order = round(float(inter_order), 1)

    first_p = metrics.get("first_purchase")
    last_p = metrics.get("last_purchase")
    first_p_str = str(first_p.date()) if hasattr(first_p, "date") else str(first_p)
    last_p_str = str(last_p.date()) if hasattr(last_p, "date") else str(last_p)

    return CustomerProfileResponse(
        customer_id=int(metrics["CustomerID"]),
        country=str(metrics.get("country", "Unknown")),
        first_purchase=first_p_str,
        last_purchase=last_p_str,
        frequency=int(metrics["frequency"]),
        monetary=round(float(metrics["monetary"]), 2),
        avg_order_value=round(float(metrics["avg_order_value"]), 2),
        avg_qty_per_order=round(float(metrics["avg_qty_per_order"]), 2),
        recency=int(metrics["recency"]),
        tenure_days=int(metrics["tenure_days"]),
        repeat_rate=int(metrics["repeat_rate"]),
        unique_products=int(metrics["unique_products"]),
        inter_order_days=inter_order,
        order_history=order_history,
        top_products=top_products,
        predictions=badges,
    )
