"""
pages/6_Recommendations.py
───────────────────────────
Product recommendation page.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
from config import APP_ICON, APP_TITLE

st.set_page_config(page_title=f"Recommendations — {APP_TITLE}", page_icon=APP_ICON, layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.section-header { font-size:1.3rem; font-weight:600; border-left:3px solid #4F8EF7;
    padding-left:0.75rem; margin:1.5rem 0 1rem; color:#E6EDF3; }
.info-box { background:rgba(79,142,247,0.07); border:1px solid rgba(79,142,247,0.25);
    border-radius:10px; padding:1rem 1.25rem; margin:1rem 0; font-size:0.9rem; }
.rec-card { background:#161B22; border:1px solid #21262D; border-radius:10px;
    padding:0.8rem 1rem; margin-bottom:0.5rem; transition:border-color 0.2s ease; }
.rec-card:hover { border-color:#4F8EF7; }
</style>
""", unsafe_allow_html=True)

st.title("💡 Product Recommendations")

if "purchase_df" not in st.session_state or st.session_state["purchase_df"] is None:
    st.warning("Load data first via ⚙️ Settings.")
    st.stop()

purchase_df = st.session_state["purchase_df"]

# ── Build recommender ─────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🔧 Build Recommender</div>", unsafe_allow_html=True)
st.markdown("""
<div class='info-box'>
    <strong>Strategies used (in priority order):</strong><br>
    1. <strong>Item-item collaborative filtering</strong> — based on customers with similar purchase patterns<br>
    2. <strong>Co-purchase association rules</strong> — "Frequently bought together" (Apriori)<br>
    3. <strong>Popularity fallback</strong> — globally popular products for cold-start / sparse history
    <br><br>
    Cancelled transactions are excluded. Products already purchased are not recommended again
    (unless explicitly requested).
</div>
""", unsafe_allow_html=True)

if st.button("▶ Build Recommender", type="primary"):
    from src.recommendations import build_recommender, evaluate_recommendations
    with st.spinner("Building recommender… (may take a minute for association rules)"):
        rec = build_recommender(purchase_df)
        rec_eval = evaluate_recommendations(purchase_df, rec)
    st.session_state["recommender"] = rec
    st.session_state["rec_eval"] = rec_eval
    st.success(
        f"✅ Recommender ready | "
        f"Hit Rate@10 = {rec_eval['hit_rate_at_n']:.3f} | "
        f"MRR@10 = {rec_eval['mrr_at_n']:.3f}"
    )
    for note in rec.notes:
        st.caption(f"ℹ {note}")

recommender = st.session_state.get("recommender")
if recommender is None:
    st.stop()

# ── Evaluation ────────────────────────────────────────────────────────────────
rec_eval = st.session_state.get("rec_eval")
if rec_eval:
    st.markdown("<div class='section-header'>📊 Offline Evaluation</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Hit Rate@{rec_eval['n']}", f"{rec_eval['hit_rate_at_n']:.3f}")
    c2.metric(f"MRR@{rec_eval['n']}", f"{rec_eval['mrr_at_n']:.3f}")
    c3.metric("Customers Evaluated", f"{rec_eval['evaluated_customers']:,}")
    st.markdown("""
    <div class='info-box'>
        <strong>Hit Rate@N</strong>: Fraction of customers for whom the held-out last product
        appears in the top-N recommendations.<br>
        <strong>MRR@N</strong>: Mean Reciprocal Rank — rewards recommendations that appear higher
        in the list. Higher is better; 0 means no hits.
    </div>
    """, unsafe_allow_html=True)

# ── Per-customer recommendations ──────────────────────────────────────────────
st.markdown("<div class='section-header'>👤 Get Recommendations for a Customer</div>", unsafe_allow_html=True)

customer_features = st.session_state.get("customer_features")
if customer_features is None:
    st.warning("Load data to see customer list.")
    st.stop()

cids = sorted(customer_features["CustomerID"].tolist())
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    selected_cid = st.selectbox("Select Customer", cids, format_func=lambda x: f"Customer {x}")
with col2:
    top_n = st.number_input("Number of recommendations", 3, 20, 10)
with col3:
    exclude = st.checkbox("Exclude already-purchased", value=True)

if st.button("Get Recommendations", type="primary"):
    from src.recommendations import get_recommendations
    recs = get_recommendations(int(selected_cid), recommender, n=int(top_n), exclude_purchased=exclude)
    if recs.empty:
        st.info("No recommendations available. This customer may have very sparse history.")
    else:
        st.markdown(f"**Top {len(recs)} recommendations for Customer {selected_cid}:**")
        for i, row in recs.iterrows():
            st.markdown(f"""
            <div class='rec-card'>
                <span style='font-weight:600; color:#E6EDF3;'>{i+1}. {row.get('Description', row['StockCode'])}</span>
                <span style='color:#8B949E; font-size:0.8rem; margin-left:0.5rem;'>({row['StockCode']})</span><br>
                <span style='color:#58A6FF; font-size:0.8rem;'>💡 {row.get('reason', 'Popular product')}</span>
            </div>
            """, unsafe_allow_html=True)

# ── Global popularity ─────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🌟 Globally Popular Products</div>", unsafe_allow_html=True)
if recommender.global_popularity is not None and recommender.product_info is not None:
    top_global = recommender.global_popularity.head(15).reset_index()
    top_global.columns = ["StockCode", "TotalQuantity"]
    top_global = top_global.merge(recommender.product_info, on="StockCode", how="left")
    st.dataframe(
        top_global[["StockCode", "Description", "TotalQuantity"]],
        use_container_width=True,
        hide_index=True,
    )

# ── Association rules preview ─────────────────────────────────────────────────
if recommender.copurchase_rules is not None:
    st.markdown("<div class='section-header'>🔗 Co-Purchase Association Rules (Top 20)</div>", unsafe_allow_html=True)
    rules = recommender.copurchase_rules.nlargest(20, "confidence")
    # Attach descriptions
    if recommender.product_info is not None:
        rules = rules.merge(
            recommender.product_info.rename(columns={"StockCode": "antecedent", "Description": "antecedent_desc"}),
            on="antecedent", how="left"
        ).merge(
            recommender.product_info.rename(columns={"StockCode": "consequent", "Description": "consequent_desc"}),
            on="consequent", how="left"
        )
    st.dataframe(
        rules[["antecedent_desc" if "antecedent_desc" in rules.columns else "antecedent",
               "consequent_desc" if "consequent_desc" in rules.columns else "consequent",
               "support", "confidence", "lift"]].rename(columns={
            "antecedent_desc": "If bought", "consequent_desc": "Also bought",
            "antecedent": "If bought", "consequent": "Also bought",
        }),
        use_container_width=True, hide_index=True,
    )

st.caption("⚠ Recommendations are data-driven suggestions. They are not guarantees of future purchases.")
