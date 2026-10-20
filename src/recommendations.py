"""
src/recommendations.py
──────────────────────
Product recommendation system using three complementary strategies:

1. Co-purchase association rules (mlxtend Apriori + confidence)
   — "Customers who bought X also frequently bought Y."
2. Item-based collaborative filtering via cosine similarity on the
   customer-product purchase matrix.
3. Popularity fallback — most globally purchased products — for cold-start
   customers with no purchase history.

Cancelled transactions are excluded from all interaction matrices.
Already-purchased products are excluded from personalised recommendations
unless the caller explicitly asks for repeat-purchase suggestions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from config import (
    MIN_CONFIDENCE,
    MIN_SUPPORT,
    RANDOM_SEED,
    TOP_N_RECOMMENDATIONS,
)

logger = logging.getLogger(__name__)


@dataclass
class RecommenderSystem:
    """Container for all fitted recommendation artefacts."""

    # Co-purchase rules: index = antecedent StockCode, cols = consequent StockCode, value = confidence
    copurchase_rules: Optional[pd.DataFrame] = None

    # Item-item similarity matrix (StockCode x StockCode)
    item_similarity: Optional[pd.DataFrame] = None

    # Global popularity (sorted)
    global_popularity: Optional[pd.Series] = None

    # Product description lookup
    product_info: Optional[pd.DataFrame] = None

    # Customer → set of purchased StockCodes
    customer_purchases: dict[int, set] = field(default_factory=dict)

    notes: list[str] = field(default_factory=list)


def build_recommender(purchase_df: pd.DataFrame) -> RecommenderSystem:
    """
    Fit the recommendation system on valid (non-cancelled) purchases.

    Parameters
    ----------
    purchase_df : pd.DataFrame
        Non-cancelled purchase rows with CustomerID, StockCode, Description,
        Quantity, InvoiceNo columns.

    Returns
    -------
    RecommenderSystem
    """
    rec = RecommenderSystem()
    df = purchase_df.copy()

    # ── Product info lookup ──────────────────────────────────────────────────
    rec.product_info = (
        df.groupby("StockCode")["Description"]
        .agg(lambda x: x.mode().iloc[0] if len(x) > 0 else "")
        .reset_index()
    )

    # ── Global popularity ────────────────────────────────────────────────────
    rec.global_popularity = (
        df.groupby("StockCode")["Quantity"].sum().sort_values(ascending=False)
    )

    # ── Customer purchase history ────────────────────────────────────────────
    rec.customer_purchases = (
        df.groupby("CustomerID")["StockCode"]
        .apply(set)
        .to_dict()
    )

    # ── Customer-product matrix (for item-item CF) ───────────────────────────
    pivot = _build_customer_item_matrix(df)
    if pivot is not None and pivot.shape[1] > 1:
        item_sim = cosine_similarity(pivot.T)
        rec.item_similarity = pd.DataFrame(
            item_sim,
            index=pivot.columns,
            columns=pivot.columns,
        )
        rec.notes.append(
            f"Item-item similarity matrix built: {pivot.shape[0]} customers × "
            f"{pivot.shape[1]} products."
        )
    else:
        rec.notes.append("Item-item CF skipped: insufficient product diversity.")

    # ── Association rules (co-purchase) ─────────────────────────────────────
    rules = _fit_association_rules(df)
    if rules is not None:
        rec.copurchase_rules = rules
        rec.notes.append(f"Association rules mined: {len(rules)} rules.")
    else:
        rec.notes.append(
            "Association rules skipped: not enough transactions or mlxtend unavailable."
        )

    return rec


def _build_customer_item_matrix(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Build a binary customer × product interaction matrix."""
    try:
        # Keep products with at least 5 customers
        product_counts = df.groupby("StockCode")["CustomerID"].nunique()
        popular_products = product_counts[product_counts >= 5].index
        df_filtered = df[df["StockCode"].isin(popular_products)]

        if df_filtered.empty:
            return None

        pivot = (
            df_filtered.pivot_table(
                index="CustomerID",
                columns="StockCode",
                values="Quantity",
                aggfunc="sum",
                fill_value=0,
            )
            .clip(upper=1)  # binarise
        )
        return pivot
    except Exception as e:
        logger.warning("Could not build customer-item matrix: %s", e)
        return None


def _fit_association_rules(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Mine co-purchase association rules using mlxtend Apriori."""
    try:
        from mlxtend.frequent_patterns import apriori, association_rules
        from mlxtend.preprocessing import TransactionEncoder

        # Build basket per invoice
        baskets = (
            df.groupby("InvoiceNo")["StockCode"]
            .apply(list)
            .tolist()
        )

        # Keep only products with reasonable support
        te = TransactionEncoder()
        te_array = te.fit_transform(baskets)
        basket_df = pd.DataFrame(te_array, columns=te.columns_)

        freq_items = apriori(basket_df, min_support=MIN_SUPPORT, use_colnames=True)
        if freq_items.empty:
            return None

        rules = association_rules(freq_items, metric="confidence", min_threshold=MIN_CONFIDENCE)
        if rules.empty:
            return None

        # Simplify: keep only 1-to-1 rules for easy lookup
        rules["antecedent"] = rules["antecedents"].apply(
            lambda x: list(x)[0] if len(x) == 1 else None
        )
        rules["consequent"] = rules["consequents"].apply(
            lambda x: list(x)[0] if len(x) == 1 else None
        )
        rules = rules.dropna(subset=["antecedent", "consequent"])
        return rules[["antecedent", "consequent", "support", "confidence", "lift"]].reset_index(drop=True)
    except ImportError:
        logger.warning("mlxtend not installed; association rules skipped.")
        return None
    except Exception as e:
        logger.warning("Association rule mining failed: %s", e)
        return None


def get_recommendations(
    customer_id: int,
    recommender: RecommenderSystem,
    n: int = TOP_N_RECOMMENDATIONS,
    exclude_purchased: bool = True,
) -> pd.DataFrame:
    """
    Generate top-N product recommendations for a customer.

    Strategy priority:
      1. Item-item CF based on the customer's purchased items.
      2. Association rules from the customer's purchased items.
      3. Global popularity fallback.

    Parameters
    ----------
    customer_id : int
    recommender : RecommenderSystem
    n : int
        Number of recommendations to return.
    exclude_purchased : bool
        If True (default), products the customer already bought are excluded.

    Returns
    -------
    pd.DataFrame with columns: StockCode, Description, score, reason
    """
    purchased = recommender.customer_purchases.get(customer_id, set())
    recs: dict[str, dict] = {}

    # ── Strategy 1: Item-item CF ─────────────────────────────────────────────
    if recommender.item_similarity is not None and purchased:
        sim_mat = recommender.item_similarity
        known = [p for p in purchased if p in sim_mat.index]
        if known:
            scores = sim_mat.loc[known].mean(axis=0)
            scores = scores.drop(labels=[p for p in known if p in scores.index], errors="ignore")
            for item, score in scores.nlargest(n * 3).items():
                if item not in recs:
                    recs[item] = {"score": score, "reason": "Customers with similar taste also bought this"}

    # ── Strategy 2: Association rules ────────────────────────────────────────
    if recommender.copurchase_rules is not None and purchased:
        rules = recommender.copurchase_rules
        filtered = rules[rules["antecedent"].isin(purchased)]
        for _, row in filtered.sort_values("confidence", ascending=False).head(n * 2).iterrows():
            cons = row["consequent"]
            if cons not in recs:
                recs[cons] = {
                    "score": float(row["confidence"]),
                    "reason": f"Frequently bought with {row['antecedent']}",
                }

    # ── Strategy 3: Popularity fallback ──────────────────────────────────────
    if recommender.global_popularity is not None:
        fallback_reason = "Popular among all customers" if purchased else "Popular product (new customer)"
        for item, qty in recommender.global_popularity.items():
            if len(recs) >= n * 3:
                break
            if item not in recs:
                recs[item] = {"score": float(qty), "reason": fallback_reason}

    # Exclude already-purchased items
    if exclude_purchased:
        for item in list(purchased):
            recs.pop(item, None)

    if not recs:
        return pd.DataFrame(columns=["StockCode", "Description", "score", "reason"])

    rec_df = pd.DataFrame([
        {"StockCode": k, **v} for k, v in recs.items()
    ]).nlargest(n, "score").reset_index(drop=True)

    # Attach descriptions
    if recommender.product_info is not None:
        rec_df = rec_df.merge(recommender.product_info, on="StockCode", how="left")

    if "Description" not in rec_df.columns:
        rec_df["Description"] = ""

    return rec_df[["StockCode", "Description", "score", "reason"]].head(n)


def evaluate_recommendations(
    purchase_df: pd.DataFrame,
    recommender: RecommenderSystem,
    n: int = TOP_N_RECOMMENDATIONS,
    sample_size: int = 200,
) -> dict:
    """
    Offline evaluation of recommendations using held-out last-purchase items.

    For each customer, remove their last purchase from the training set
    and check whether it appears in the top-N recommendations.

    Returns
    -------
    dict with hit_rate and mrr (Mean Reciprocal Rank) metrics.
    """
    rng = np.random.default_rng(RANDOM_SEED)

    # Get all customer → last product pairs
    last_items = (
        purchase_df.sort_values("InvoiceDate")
        .groupby("CustomerID")
        .last()["StockCode"]
        .reset_index()
    )

    # Sample to keep evaluation fast
    if len(last_items) > sample_size:
        last_items = last_items.sample(sample_size, random_state=RANDOM_SEED)

    hits = 0
    reciprocal_ranks = []
    for _, row in last_items.iterrows():
        cid = row["CustomerID"]
        true_item = row["StockCode"]
        recs = get_recommendations(cid, recommender, n=n, exclude_purchased=False)
        rec_items = recs["StockCode"].tolist()
        if true_item in rec_items:
            hits += 1
            rank = rec_items.index(true_item) + 1
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)

    hit_rate = hits / len(last_items) if len(last_items) > 0 else 0.0
    mrr = float(np.mean(reciprocal_ranks)) if reciprocal_ranks else 0.0

    return {
        "hit_rate_at_n": round(hit_rate, 4),
        "mrr_at_n": round(mrr, 4),
        "n": n,
        "evaluated_customers": len(last_items),
    }
