"""
backend/app/api/routes/models.py
Consolidated model status, scorecard, and training orchestrator.
"""

from fastapi import APIRouter, HTTPException
from backend.app.core.state import state
from src.segmentation import train_segmentation
from src.churn_prediction import train_churn_model
from src.next_purchase import train_next_purchase_model
from src.recommendations import build_recommender, evaluate_recommendations

router = APIRouter()


@router.get("/summary")
def get_models_summary():
    if not state.is_data_loaded:
        raise HTTPException(status_code=400, detail="Dataset not loaded.")

    seg = state.segmentation_result
    churn = state.churn_result
    np_res = state.next_purchase_result
    rec_eval = state.rec_eval

    return {
        "dataset_ready": True,
        "segmentation": {
            "is_trained": seg is not None,
            "n_clusters": seg.n_clusters if seg else 0,
            "silhouette": round(seg.silhouette, 3) if seg else 0.0,
            "methodology": "K-Means on RFM + Basket Depth with Silhouette & Elbow validation.",
        },
        "next_purchase": {
            "is_trained": np_res is not None and np_res.best_pipeline is not None,
            "best_model": np_res.best_model_name if np_res else "None",
            "model_mae": round(np_res.model_mae, 1) if np_res else 0.0,
            "baseline_mae": round(np_res.baseline_mae, 1) if np_res else 0.0,
            "mae_improvement_pct": round(np_res.mae_improvement_pct, 1) if np_res else 0.0,
            "methodology": "Chronological inter-order sequence formulation with no forward-looking target leakage.",
        },
        "churn": {
            "is_trained": churn is not None and churn.best_pipeline is not None,
            "best_model": churn.best_model_name if churn else "None",
            "roc_auc": round(max(churn.lr_auc, churn.rf_auc), 3) if churn else 0.0,
            "churn_rate": round(churn.churn_rate, 3) if churn else 0.0,
            "methodology": "Strict out-of-time historical cutoff separating observation window from churn horizon.",
        },
        "recommendations": {
            "is_built": state.recommender is not None,
            "hit_rate_at_10": round(rec_eval["hit_rate_at_n"], 3) if rec_eval else 0.0,
            "mrr_at_10": round(rec_eval["mrr_at_n"], 3) if rec_eval else 0.0,
            "methodology": "Item-Item Cosine Similarity + Apriori Association Rules with popularity fallback.",
        },
    }


@router.post("/train-all")
def train_all_models():
    if not state.is_data_loaded:
        raise HTTPException(status_code=400, detail="Dataset not loaded.")

    purchase_df = state.purchase_df
    customer_features = state.customer_features

    # 1. Segmentation
    seg = train_segmentation(customer_features)
    state.segmentation_result = seg

    # 2. Churn
    churn = train_churn_model(purchase_df)
    state.churn_result = churn

    # 3. Next purchase
    npp = train_next_purchase_model(purchase_df)
    state.next_purchase_result = npp

    # 4. Recommender
    rec = build_recommender(purchase_df)
    state.recommender = rec
    rec_eval = evaluate_recommendations(purchase_df, rec)
    state.rec_eval = rec_eval

    return {
        "success": True,
        "message": "All 4 models successfully trained on active dataset.",
        "segmentation_clusters": seg.n_clusters,
        "churn_auc": round(max(churn.lr_auc, churn.rf_auc), 3) if churn.best_pipeline else 0.0,
        "next_purchase_mae": round(npp.model_mae, 1) if npp.best_pipeline else 0.0,
        "recommendation_hit_rate": round(rec_eval["hit_rate_at_n"], 3),
    }
