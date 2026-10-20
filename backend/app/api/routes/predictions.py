"""
backend/app/api/routes/predictions.py
Machine learning prediction routes for Next Purchase regression & Churn classification.
"""

from datetime import timedelta
import io
import math
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from sklearn.metrics import roc_curve

from backend.app.core.state import state
from backend.app.schemas.predictions import (
    NextPurchaseMetricsResponse,
    NextPurchaseEstimateRequest,
    NextPurchaseEstimateResponse,
    BatchNextPurchaseItem,
    ChurnMetricsResponse,
    AtRiskCustomerItem,
    TrainChurnRequest,
    ROCCurvePoint,
    ConfusionMatrixData,
    FeatureImportanceItem,
)
from src.next_purchase import (
    train_next_purchase_model,
    predict_next_purchase,
)
from src.churn_prediction import (
    train_churn_model,
    predict_churn,
    churn_risk_category,
)

router = APIRouter()


# ── Next Purchase Endpoints ──

@router.post("/next-purchase/train", response_model=NextPurchaseMetricsResponse)
def train_next_purchase():
    if state.purchase_df is None:
        raise HTTPException(status_code=400, detail="Dataset not loaded.")

    res = train_next_purchase_model(state.purchase_df)
    state.next_purchase_result = res

    if res.best_pipeline is None:
        return NextPurchaseMetricsResponse(
            is_trained=False,
            best_model_name="None",
            model_mae=0.0,
            model_rmse=0.0,
            model_r2=0.0,
            baseline_mae=0.0,
            mae_improvement_pct=0.0,
            sample_count=0,
            feature_importances=[],
            notes=res.notes,
        )

    fi = [
        FeatureImportanceItem(feature=feat, importance=round(float(imp), 4))
        for feat, imp in res.feature_importances.items()
    ]

    mae_imp = 0.0
    if res.baseline_mae > 0:
        mae_imp = (res.baseline_mae - res.model_mae) / res.baseline_mae * 100

    return NextPurchaseMetricsResponse(
        is_trained=True,
        best_model_name=res.best_model_name,
        model_mae=round(res.model_mae, 2),
        model_rmse=round(res.model_rmse, 2),
        model_r2=round(getattr(res, "model_r2", 0.0), 3),
        baseline_mae=round(res.baseline_mae, 2),
        mae_improvement_pct=round(mae_imp, 1),
        sample_count=res.training_samples + res.test_samples,
        feature_importances=fi,
        notes=res.notes,
    )


@router.get("/next-purchase/metrics", response_model=NextPurchaseMetricsResponse)
def get_next_purchase_metrics():
    if state.next_purchase_result is None:
        if state.purchase_df is not None:
            return train_next_purchase()
        raise HTTPException(status_code=400, detail="Next purchase model not trained.")

    res = state.next_purchase_result
    fi = [
        FeatureImportanceItem(feature=feat, importance=round(float(imp), 4))
        for feat, imp in res.feature_importances.items()
    ]
    mae_imp = 0.0
    if res.baseline_mae > 0:
        mae_imp = (res.baseline_mae - res.model_mae) / res.baseline_mae * 100

    return NextPurchaseMetricsResponse(
        is_trained=res.best_pipeline is not None,
        best_model_name=res.best_model_name,
        model_mae=round(res.model_mae, 2),
        model_rmse=round(res.model_rmse, 2),
        model_r2=round(getattr(res, "model_r2", 0.0), 3),
        baseline_mae=round(res.baseline_mae, 2),
        mae_improvement_pct=round(mae_imp, 1),
        sample_count=res.training_samples + res.test_samples,
        feature_importances=fi,
        notes=res.notes,
    )


@router.post("/next-purchase/estimate", response_model=NextPurchaseEstimateResponse)
def estimate_next_purchase(req: NextPurchaseEstimateRequest):
    if state.next_purchase_result is None or state.next_purchase_result.best_pipeline is None:
        raise HTTPException(status_code=400, detail="Next purchase model not trained.")

    cust_rows = state.purchase_df[state.purchase_df["CustomerID"] == req.customer_id]
    if cust_rows.empty:
        raise HTTPException(status_code=404, detail="Customer ID not found.")

    pred = predict_next_purchase(
        customer_id=req.customer_id,
        purchase_df=state.purchase_df,
        result=state.next_purchase_result,
    )
    if pred is None or math.isnan(pred):
        raise HTTPException(status_code=400, detail="Insufficient purchase history to make prediction.")

    last_date = cust_rows["InvoiceDate"].max()
    est_date = last_date + timedelta(days=float(pred))

    return NextPurchaseEstimateResponse(
        customer_id=req.customer_id,
        predicted_days=round(float(pred), 1),
        predicted_date=str(est_date.date()),
        model_used=state.next_purchase_result.best_model_name,
        confidence_note=f"Estimated based on {cust_rows['InvoiceNo'].nunique()} past orders and inter-order cadence.",
    )


@router.get("/next-purchase/batch", response_model=list[BatchNextPurchaseItem])
def get_batch_next_purchase(limit: int = Query(50, ge=10, le=500)):
    if state.next_purchase_result is None or state.next_purchase_result.best_pipeline is None:
        raise HTTPException(status_code=400, detail="Next purchase model not trained.")

    if state.customer_features is None:
        return []

    now = state.purchase_df["InvoiceDate"].max()
    sample_cids = state.customer_features["CustomerID"].head(limit).tolist()
    items = []

    for cid in sample_cids:
        pred = predict_next_purchase(int(cid), state.purchase_df, state.next_purchase_result)
        if pred is not None and not math.isnan(pred):
            cust_df = state.purchase_df[state.purchase_df["CustomerID"] == cid]
            last_d = cust_df["InvoiceDate"].max()
            est_d = last_d + timedelta(days=float(pred))
            diff = (est_d - now).days
            status = "Overdue" if diff < 0 else "Due Soon" if diff <= 14 else "On Track"
            items.append(
                BatchNextPurchaseItem(
                    customer_id=int(cid),
                    last_purchase_date=str(last_d.date()),
                    predicted_days=round(float(pred), 1),
                    predicted_next_date=str(est_d.date()),
                    status=status,
                )
            )
    return items


# ── Churn Endpoints ──

def _build_churn_response(res) -> ChurnMetricsResponse:
    if res.best_pipeline is None:
        return ChurnMetricsResponse(
            is_trained=False,
            best_model_name="None",
            churn_rate=0.0,
            lr_auc=0.0,
            rf_auc=0.0,
            best_auc=0.0,
            precision=0.0,
            recall=0.0,
            f1=0.0,
            train_size=0,
            test_size=0,
            roc_curve=[],
            confusion_matrix=ConfusionMatrixData(tn=0, fp=0, fn=0, tp=0, threshold=0.5),
            feature_importances=[],
            notes=res.notes,
        )

    # ROC curve points
    fpr, tpr, _ = roc_curve(res.test_labels, res.best_probas)
    step = max(1, len(fpr) // 30)
    roc_pts = [
        ROCCurvePoint(fpr=round(float(f), 3), tpr=round(float(t), 3))
        for f, t in zip(fpr[::step], tpr[::step])
    ]

    cm = res.confusion
    cm_data = ConfusionMatrixData(
        tn=int(cm[0, 0]),
        fp=int(cm[0, 1]),
        fn=int(cm[1, 0]),
        tp=int(cm[1, 1]),
        threshold=0.5,
    )

    fi = [
        FeatureImportanceItem(feature=feat, importance=round(float(imp), 4))
        for feat, imp in res.feature_importances.items()
    ]

    # Get precision / recall / f1 from report
    report = res.rf_report if res.best_model_name == "Random Forest" else res.lr_report
    w_avg = report.get("weighted avg", {})

    return ChurnMetricsResponse(
        is_trained=True,
        best_model_name=res.best_model_name,
        churn_rate=round(res.churn_rate, 3),
        lr_auc=round(res.lr_auc, 3),
        rf_auc=round(res.rf_auc, 3),
        best_auc=round(max(res.lr_auc, res.rf_auc), 3),
        precision=round(float(w_avg.get("precision", 0.0)), 3),
        recall=round(float(w_avg.get("recall", 0.0)), 3),
        f1=round(float(w_avg.get("f1-score", 0.0)), 3),
        train_size=res.training_samples,
        test_size=res.test_samples,
        roc_curve=roc_pts,
        confusion_matrix=cm_data,
        feature_importances=fi,
        notes=res.notes,
    )


@router.post("/churn/train", response_model=ChurnMetricsResponse)
def train_churn(req: TrainChurnRequest = TrainChurnRequest()):
    if state.purchase_df is None:
        raise HTTPException(status_code=400, detail="Dataset not loaded.")

    res = train_churn_model(
        state.purchase_df,
        churn_window_days=req.churn_window_days,
    )
    state.churn_result = res
    return _build_churn_response(res)


@router.get("/churn/metrics", response_model=ChurnMetricsResponse)
def get_churn_metrics():
    if state.churn_result is None:
        if state.purchase_df is not None:
            return train_churn()
        raise HTTPException(status_code=400, detail="Churn model not trained.")

    return _build_churn_response(state.churn_result)


@router.get("/churn/at-risk", response_model=list[AtRiskCustomerItem])
def get_at_risk_list(
    threshold: float = Query(0.5, ge=0.1, le=0.9),
    limit: int = Query(50, ge=10, le=500),
):
    if state.churn_result is None or state.churn_result.best_pipeline is None:
        raise HTTPException(status_code=400, detail="Churn model not trained.")

    if state.customer_features is None:
        return []

    rows = []
    for _, r in state.customer_features.iterrows():
        cid = int(r["CustomerID"])
        p = predict_churn(cid, state.purchase_df, state.churn_result)
        if p is not None and p >= threshold:
            risk = churn_risk_category(p)
            rows.append(
                AtRiskCustomerItem(
                    customer_id=cid,
                    churn_probability=round(float(p), 3),
                    risk_level=risk,
                    recency_days=int(r["recency"]),
                    frequency=int(r["frequency"]),
                    monetary=round(float(r["monetary"]), 2),
                    country=str(r.get("country", "United Kingdom")),
                )
            )

    rows.sort(key=lambda x: x.churn_probability, reverse=True)
    return rows[:limit]


@router.get("/churn/export-at-risk")
def export_at_risk_csv(threshold: float = 0.5):
    if state.churn_result is None or state.churn_result.best_pipeline is None:
        raise HTTPException(status_code=400, detail="Churn model not trained.")

    rows = []
    for _, r in state.customer_features.iterrows():
        cid = int(r["CustomerID"])
        p = predict_churn(cid, state.purchase_df, state.churn_result)
        if p is not None and p >= threshold:
            rows.append({
                "CustomerID": cid,
                "churn_probability": round(float(p), 4),
                "risk_category": churn_risk_category(p),
                "recency": r["recency"],
                "frequency": r["frequency"],
                "monetary": r["monetary"],
            })
    df = pd.DataFrame(rows).sort_values("churn_probability", ascending=False)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=at_risk_customers.csv"},
    )
