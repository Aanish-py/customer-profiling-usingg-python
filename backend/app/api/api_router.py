"""
backend/app/api/api_router.py
Aggregates all API route modules under the main router.
"""

from fastapi import APIRouter

from backend.app.api.routes import (
    health,
    dataset,
    analytics,
    customers,
    segmentation,
    predictions,
    recommendations,
    models,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(dataset.router, prefix="/dataset", tags=["Dataset"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
api_router.include_router(segmentation.router, prefix="/segmentation", tags=["Segmentation"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
api_router.include_router(models.router, prefix="/models", tags=["Models"])
