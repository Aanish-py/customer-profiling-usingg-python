"""
backend/app/api/routes/health.py
Health check and system status.
"""

from fastapi import APIRouter
from backend.app.core.state import state

router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "dataset_loaded": state.is_data_loaded,
        "models_trained": {
            "segmentation": state.segmentation_result is not None,
            "churn": state.churn_result is not None,
            "next_purchase": state.next_purchase_result is not None,
            "recommender": state.recommender is not None,
        },
    }
