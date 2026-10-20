"""
backend/app/api/routes/segmentation.py
K-Means customer segmentation and PCA visualization routes.
"""

import io
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from backend.app.core.state import state
from backend.app.schemas.segmentation import (
    SegmentationCurvesResponse,
    SegmentationResultResponse,
    ClusterProfileItem,
    PCAPoint,
    TrainSegmentationRequest,
    CurvePoint,
)
from src.segmentation import (
    train_segmentation,
    cluster_profile_table,
    assign_segments,
)

router = APIRouter()


def _format_segmentation_response(result) -> SegmentationResultResponse:
    customer_features = state.customer_features
    profile_df = cluster_profile_table(customer_features, result)
    total_cust = len(customer_features)

    profiles = []
    for _, row in profile_df.iterrows():
        seg_name = str(row["segment"])
        count = int(row.get("customer_count", 0))
        pct = round(count / total_cust * 100, 1) if total_cust else 0.0

        # Find cluster id for this segment name
        cluster_id = 0
        for cid, cname in result.segment_names.items():
            if cname == seg_name:
                cluster_id = cid
                break

        profiles.append(
            ClusterProfileItem(
                cluster=cluster_id,
                name=seg_name,
                count=count,
                pct_customers=pct,
                mean_recency=round(float(row.get("recency", 0)), 1),
                mean_frequency=round(float(row.get("frequency", 0)), 1),
                mean_monetary=round(float(row.get("monetary", 0)), 2),
                mean_aov=round(float(row.get("avg_order_value", 0)), 2),
                description=f"{seg_name} ({pct}% of customer base)",
            )
        )

    # PCA Points
    pca_points = []
    pca_arr = result.pca_coords
    labels = result.labels
    cids = customer_features["CustomerID"].values
    monetary = customer_features["monetary"].values
    freq = customer_features["frequency"].values
    rec = customer_features["recency"].values

    sample_size = min(2000, len(customer_features))
    indices = np.random.choice(len(customer_features), size=sample_size, replace=False) if len(customer_features) > sample_size else range(len(customer_features))

    for idx in indices:
        cid_label = int(labels[idx])
        cname = result.segment_names.get(cid_label, f"Cluster {cid_label}")
        pca_points.append(
            PCAPoint(
                customer_id=int(cids[idx]),
                pca1=round(float(pca_arr[idx, 0]), 3),
                pca2=round(float(pca_arr[idx, 1]), 3),
                cluster=cid_label,
                cluster_name=cname,
                monetary=round(float(monetary[idx]), 2),
                frequency=int(freq[idx]),
                recency=int(rec[idx]),
            )
        )

    max_sil = max(result.silhouette_scores.values()) if result.silhouette_scores else 0.0

    return SegmentationResultResponse(
        n_clusters=result.n_clusters,
        silhouette_score=round(float(max_sil), 3),
        profiles=profiles,
        pca_points=pca_points,
    )


@router.get("/curves", response_model=SegmentationCurvesResponse)
def get_segmentation_curves():
    if state.customer_features is None:
        raise HTTPException(status_code=400, detail="Customer features not computed.")

    if state.segmentation_result is None:
        result = train_segmentation(state.customer_features)
        state.segmentation_result = result
    else:
        result = state.segmentation_result

    inertias = result.inertias
    silhouettes = result.silhouette_scores

    elbow_curve = [CurvePoint(k=k, score=round(float(v), 1)) for k, v in inertias.items()]
    silhouette_curve = [CurvePoint(k=k, score=round(float(v), 3)) for k, v in silhouettes.items()]
    best_k = max(silhouettes, key=silhouettes.get) if silhouettes else result.n_clusters

    return SegmentationCurvesResponse(
        elbow_curve=elbow_curve,
        silhouette_curve=silhouette_curve,
        recommended_k=best_k,
    )


@router.post("/train", response_model=SegmentationResultResponse)
def train_segmentation_model(req: TrainSegmentationRequest = TrainSegmentationRequest()):
    if state.customer_features is None:
        raise HTTPException(status_code=400, detail="Customer features not computed.")

    k = int(req.n_clusters) if req.n_clusters and req.n_clusters > 1 else None
    result = train_segmentation(state.customer_features, n_clusters=k)
    state.segmentation_result = result
    return _format_segmentation_response(result)


@router.get("/results", response_model=SegmentationResultResponse)
def get_current_segmentation():
    if state.segmentation_result is None:
        if state.customer_features is not None:
            return train_segmentation_model()
        raise HTTPException(status_code=400, detail="Segmentation model not trained yet.")

    return _format_segmentation_response(state.segmentation_result)


@router.get("/export-clusters")
def export_clusters_csv():
    if state.segmentation_result is None or state.customer_features is None:
        raise HTTPException(status_code=400, detail="Segmentation model not trained.")
    df = assign_segments(state.customer_features, state.segmentation_result)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=customer_segments.csv"},
    )
