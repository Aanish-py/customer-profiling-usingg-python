"""
backend/app/api/routes/recommendations.py
Product recommendation engine and association rules routes.
"""

from fastapi import APIRouter, HTTPException, Query
import pandas as pd

from backend.app.core.state import state
from backend.app.schemas.recommendations import (
    RecommendationEvaluationResponse,
    CustomerRecommendationsResponse,
    ProductRecommendation,
    AssociationRuleItem,
    PopularProductItem,
    BuildRecommenderRequest,
)
from src.recommendations import (
    build_recommender,
    evaluate_recommendations,
    get_recommendations,
)

router = APIRouter()


@router.post("/build", response_model=RecommendationEvaluationResponse)
def build_recommender_system(req: BuildRecommenderRequest = BuildRecommenderRequest()):
    if state.purchase_df is None:
        raise HTTPException(status_code=400, detail="Dataset not loaded.")

    rec = build_recommender(state.purchase_df)
    state.recommender = rec

    eval_res = evaluate_recommendations(state.purchase_df, rec, n=req.top_n)
    state.rec_eval = eval_res

    catalog_size = len(rec.product_info) if rec.product_info is not None else 0

    return RecommendationEvaluationResponse(
        is_built=True,
        hit_rate_at_n=round(eval_res.get("hit_rate_at_n", 0.0), 3),
        mrr_at_n=round(eval_res.get("mrr_at_n", 0.0), 3),
        catalog_size=catalog_size,
        test_customers_evaluated=eval_res.get("evaluated_customers", 0),
        top_n=eval_res.get("n", req.top_n),
    )


@router.get("/evaluation", response_model=RecommendationEvaluationResponse)
def get_recommendation_evaluation():
    if state.recommender is None:
        if state.purchase_df is not None:
            return build_recommender_system()
        raise HTTPException(status_code=400, detail="Recommender not built.")

    eval_res = state.rec_eval or {
        "hit_rate_at_n": 0.0,
        "mrr_at_n": 0.0,
        "n": 10,
        "evaluated_customers": 0,
    }
    catalog_size = len(state.recommender.product_info) if state.recommender.product_info is not None else 0

    return RecommendationEvaluationResponse(
        is_built=True,
        hit_rate_at_n=round(eval_res.get("hit_rate_at_n", 0.0), 3),
        mrr_at_n=round(eval_res.get("mrr_at_n", 0.0), 3),
        catalog_size=catalog_size,
        test_customers_evaluated=eval_res.get("evaluated_customers", 0),
        top_n=eval_res.get("n", 10),
    )


@router.get("/customer/{customer_id}", response_model=CustomerRecommendationsResponse)
def get_customer_recs(
    customer_id: int,
    top_n: int = Query(5, ge=1, le=20),
    exclude_purchased: bool = Query(True),
):
    if state.recommender is None:
        if state.purchase_df is not None:
            build_recommender_system()
        else:
            raise HTTPException(status_code=400, detail="Recommender not built.")

    rec_df = get_recommendations(
        customer_id=customer_id,
        recommender=state.recommender,
        n=top_n,
        exclude_purchased=exclude_purchased,
    )

    items = []
    if isinstance(rec_df, pd.DataFrame) and not rec_df.empty:
        for _, row in rec_df.iterrows():
            items.append(
                ProductRecommendation(
                    stock_code=str(row["StockCode"]),
                    description=str(row.get("Description", row["StockCode"])),
                    score=round(float(row.get("score", 0.0)), 2),
                    reason=str(row.get("reason", "Recommended product")),
                )
            )
    return CustomerRecommendationsResponse(customer_id=customer_id, recommendations=items)


@router.get("/rules", response_model=list[AssociationRuleItem])
def get_association_rules_list(limit: int = Query(30, ge=5, le=100)):
    if state.recommender is None:
        if state.purchase_df is not None:
            build_recommender_system()
        else:
            return []

    rules_df = state.recommender.copurchase_rules
    if rules_df is None or rules_df.empty:
        return []

    sample = rules_df.nlargest(limit, "confidence") if "confidence" in rules_df.columns else rules_df.head(limit)
    items = []
    for _, row in sample.iterrows():
        ant = [str(row["antecedent"])] if "antecedent" in row else ["Item"]
        con = [str(row["consequent"])] if "consequent" in row else ["Item"]
        items.append(
            AssociationRuleItem(
                antecedents=ant,
                consequents=con,
                support=round(float(row.get("support", 0.0)), 4),
                confidence=round(float(row.get("confidence", 0.0)), 3),
                lift=round(float(row.get("lift", 1.0)), 2),
            )
        )
    return items


@router.get("/top-products", response_model=list[PopularProductItem])
def get_popular_products(limit: int = Query(15, ge=5, le=50)):
    if state.recommender is None or state.recommender.global_popularity is None:
        if state.purchase_df is not None:
            build_recommender_system()
        else:
            return []

    rec = state.recommender
    top_global = rec.global_popularity.head(limit).reset_index()
    top_global.columns = ["StockCode", "TotalQuantity"]
    if rec.product_info is not None:
        top_global = top_global.merge(rec.product_info, on="StockCode", how="left")

    return [
        PopularProductItem(
            stock_code=str(row["StockCode"]),
            description=str(row.get("Description", row["StockCode"])),
            total_qty=int(row["TotalQuantity"]),
            order_count=0,
        )
        for _, row in top_global.iterrows()
    ]
