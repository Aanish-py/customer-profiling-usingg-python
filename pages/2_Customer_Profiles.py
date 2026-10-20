"""
pages/2_Customer_Profiles.py
─────────────────────────────
Per-customer deep-dive: RFM metrics, order history, top products,
segment, churn risk, and recommendations.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
from config import APP_ICON, APP_TITLE

st.set_page_config(page_title=f"Customer Profiles — {APP_TITLE}", page_icon=APP_ICON, layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.section-header { font-size:1.3rem; font-weight:600; border-left:3px solid #4F8EF7;
    padding-left:0.75rem; margin:1.5rem 0 1rem; color:#E6EDF3; }
.metric-card { background:#161B22; border:1px solid #21262D; border-radius:12px;
    padding:1rem; text-align:center; }
.metric-val { font-size:1.6rem; font-weight:700; color:#58A6FF; }
.metric-lbl { font-size:0.72rem; color:#8B949E; text-transform:uppercase; letter-spacing:0.06em; }
.info-box { background:rgba(79,142,247,0.07); border:1px solid rgba(79,142,247,0.25);
    border-radius:10px; padding:1rem 1.25rem; margin:1rem 0; font-size:0.9rem; }
</style>
""", unsafe_allow_html=True)

st.title("👤 Customer Profiles")

if "clean_df" not in st.session_state or st.session_state["clean_df"] is None:
    st.warning("No dataset loaded. Please go to ⚙️ Settings.")
    st.stop()

clean_df = st.session_state["clean_df"]
customer_features = st.session_state.get("customer_features")

if customer_features is None:
    st.warning("Customer features not built yet. Please load data in ⚙️ Settings first.")
    st.stop()

# ── Customer search ───────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🔍 Find a Customer</div>", unsafe_allow_html=True)

all_customer_ids = sorted(customer_features["CustomerID"].tolist())
col1, col2 = st.columns([3, 1])
with col1:
    search_val = st.selectbox(
        "Select or type a CustomerID",
        options=all_customer_ids,
        index=0,
        format_func=lambda x: f"Customer {x}",
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    show_btn = st.button("Show Profile", type="primary", use_container_width=True)

customer_id = int(search_val)

# ── Profile display ───────────────────────────────────────────────────────────
row = customer_features[customer_features["CustomerID"] == customer_id]
if row.empty:
    st.error(f"Customer {customer_id} not found.")
    st.stop()

metrics = row.iloc[0]

# Segment
seg_result = st.session_state.get("segmentation_result")
segment_label = None
if seg_result is not None:
    from src.segmentation import assign_segments
    seg_df = assign_segments(customer_features, seg_result)
    cust_seg = seg_df[seg_df["CustomerID"] == customer_id]
    if not cust_seg.empty:
        segment_label = cust_seg.iloc[0].get("segment", None)

# Churn
churn_result = st.session_state.get("churn_result")
churn_proba = None
if churn_result is not None and churn_result.best_pipeline is not None:
    from src.churn_prediction import predict_churn, churn_risk_category
    purchase_df = st.session_state.get("purchase_df", clean_df[~clean_df["is_cancelled"]])
    churn_proba = predict_churn(customer_id, purchase_df, churn_result)

# Next purchase
npp_result = st.session_state.get("next_purchase_result")
next_purchase_days = None
if npp_result is not None and npp_result.best_pipeline is not None:
    from src.next_purchase import predict_next_purchase
    purchase_df = st.session_state.get("purchase_df", clean_df[~clean_df["is_cancelled"]])
    next_purchase_days = predict_next_purchase(customer_id, purchase_df, npp_result)

# Orders
from src.customer_profiling import get_customer_orders
purchase_df_full = st.session_state.get("purchase_df", clean_df[~clean_df["is_cancelled"]])
cust_purchases = purchase_df_full[purchase_df_full["CustomerID"] == customer_id]
orders = get_customer_orders(cust_purchases)

# ── Display ───────────────────────────────────────────────────────────────────
st.markdown(f"<div class='section-header'>Customer {customer_id}</div>", unsafe_allow_html=True)

# Top KPI strip
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-val'>{int(metrics.get('recency', 0))}d</div>
        <div class='metric-lbl'>Recency</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-val'>{int(metrics.get('frequency', 0))}</div>
        <div class='metric-lbl'>Orders</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-val'>£{metrics.get('monetary', 0):,.0f}</div>
        <div class='metric-lbl'>Total Spend</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-val'>£{metrics.get('avg_order_value', 0):,.0f}</div>
        <div class='metric-lbl'>Avg Order</div>
    </div>""", unsafe_allow_html=True)
with c5:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-val'>{int(metrics.get('unique_products', 0))}</div>
        <div class='metric-lbl'>Unique Products</div>
    </div>""", unsafe_allow_html=True)
with c6:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-val'>{int(metrics.get('tenure_days', 0))}d</div>
        <div class='metric-lbl'>Tenure</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Segment, churn, next purchase
col1, col2, col3 = st.columns(3)
with col1:
    if segment_label:
        st.markdown(f"""
        <div style='background:rgba(79,142,247,0.1); border:1px solid rgba(79,142,247,0.3);
                    border-radius:10px; padding:0.8rem 1rem;'>
            <div style='font-size:0.75rem; color:#8B949E; text-transform:uppercase;'>Segment</div>
            <div style='font-size:1.1rem; font-weight:600; color:#58A6FF; margin-top:0.3rem;'>
                🎯 {segment_label}
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.info("Run segmentation to see segment.")

with col2:
    if churn_proba is not None:
        from src.churn_prediction import churn_risk_category
        risk = churn_risk_category(churn_proba)
        color = "#F85149" if risk == "High Risk" else ("#D29922" if risk == "Medium Risk" else "#3FB950")
        st.markdown(f"""
        <div style='background:rgba(248,81,73,0.08); border:1px solid rgba(248,81,73,0.3);
                    border-radius:10px; padding:0.8rem 1rem;'>
            <div style='font-size:0.75rem; color:#8B949E; text-transform:uppercase;'>Churn Risk</div>
            <div style='font-size:1.1rem; font-weight:600; color:{color}; margin-top:0.3rem;'>
                🚨 {risk} ({churn_proba:.1%})
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.info("Train churn model to see risk estimate.")

with col3:
    if next_purchase_days is not None:
        st.markdown(f"""
        <div style='background:rgba(63,185,80,0.08); border:1px solid rgba(63,185,80,0.3);
                    border-radius:10px; padding:0.8rem 1rem;'>
            <div style='font-size:0.75rem; color:#8B949E; text-transform:uppercase;'>Next Purchase Est.</div>
            <div style='font-size:1.1rem; font-weight:600; color:#3FB950; margin-top:0.3rem;'>
                📅 ~{next_purchase_days:.0f} days
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.info("Train next-purchase model for an estimate.")

# ── Order history ─────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📋 Order History</div>", unsafe_allow_html=True)
if not orders.empty:
    from src.visualizations import spending_over_time
    st.plotly_chart(spending_over_time(orders), use_container_width=True)
    st.dataframe(
        orders.style.format({"Revenue": "£{:,.2f}", "Items": "{:,.0f}"}),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No valid purchase history for this customer.")

# ── Top products ──────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🏆 Most Purchased Products</div>", unsafe_allow_html=True)
from src.customer_profiling import _top_products
top_prods = _top_products(cust_purchases)
if not top_prods.empty:
    st.dataframe(
        top_prods.style.format({"Quantity": "{:,.0f}", "Revenue": "£{:,.2f}"}),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No product data available.")

# ── Recommendations ───────────────────────────────────────────────────────────
recommender = st.session_state.get("recommender")
if recommender is not None:
    st.markdown("<div class='section-header'>💡 Product Recommendations</div>", unsafe_allow_html=True)
    from src.recommendations import get_recommendations
    recs = get_recommendations(customer_id, recommender)
    if not recs.empty:
        st.dataframe(
            recs[["StockCode", "Description", "reason"]].rename(
                columns={"StockCode": "Product Code", "Description": "Product", "reason": "Why Recommended"}
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.caption("⚠ Recommendations are data-driven suggestions, not guaranteed purchases.")
    else:
        st.info("No recommendations could be generated for this customer.")
else:
    st.info("Train the recommender (⚙️ Settings) to see product suggestions.")

# ── Download ──────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>⬇ Download</div>", unsafe_allow_html=True)
if not orders.empty:
    csv = orders.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Order History CSV",
        data=csv,
        file_name=f"customer_{customer_id}_orders.csv",
        mime="text/csv",
    )
