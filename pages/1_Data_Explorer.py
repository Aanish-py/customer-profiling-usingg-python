"""
pages/1_Data_Explorer.py
─────────────────────────
Exploratory Data Analysis page.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
from config import APP_ICON, APP_TITLE

st.set_page_config(page_title=f"Data Explorer — {APP_TITLE}", page_icon=APP_ICON, layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.section-header { font-size:1.3rem; font-weight:600; border-left:3px solid #4F8EF7;
    padding-left:0.75rem; margin:1.5rem 0 1rem; color:#E6EDF3; }
.info-box { background:rgba(79,142,247,0.07); border:1px solid rgba(79,142,247,0.25);
    border-radius:10px; padding:1rem 1.25rem; margin:1rem 0; font-size:0.9rem; }
</style>
""", unsafe_allow_html=True)

st.title("🔍 Data Explorer")

if "clean_df" not in st.session_state or st.session_state["clean_df"] is None:
    st.warning("No dataset loaded. Please go to ⚙️ Settings and load the dataset first.")
    st.stop()

clean_df = st.session_state["clean_df"]
purchase_df = st.session_state.get("purchase_df", clean_df[~clean_df["is_cancelled"]])
customer_features = st.session_state.get("customer_features")
report = st.session_state.get("preprocessing_report")

# ── Preprocessing Report ──────────────────────────────────────────────────────
if report:
    st.markdown("<div class='section-header'>🧹 Preprocessing Report</div>", unsafe_allow_html=True)
    st.dataframe(report.summary_df(), use_container_width=True, hide_index=True)

# ── Raw data sample ───────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📄 Raw Data Sample</div>", unsafe_allow_html=True)
n_sample = st.slider("Rows to display", 5, 500, 50)
st.dataframe(clean_df.head(n_sample), use_container_width=True)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Clean Rows", f"{len(clean_df):,}")
col2.metric("Customers", f"{clean_df['CustomerID'].nunique():,}")
col3.metric("Products", f"{clean_df['StockCode'].nunique():,}")
col4.metric("Countries", f"{clean_df['Country'].nunique():,}")

# ── EDA Charts ────────────────────────────────────────────────────────────────
from src.visualizations import (
    monthly_revenue_chart,
    monthly_orders_chart,
    top_products_chart,
    revenue_by_country_chart,
    order_value_distribution,
    purchase_frequency_distribution,
    repeat_vs_onetime_chart,
    customer_spending_distribution,
)

st.markdown("<div class='section-header'>📈 Revenue Trends</div>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(monthly_revenue_chart(clean_df), use_container_width=True)
with col2:
    st.plotly_chart(monthly_orders_chart(clean_df), use_container_width=True)

st.markdown("<div class='section-header'>🏆 Top Products</div>", unsafe_allow_html=True)
metric_choice = st.radio("Rank by", ["Revenue", "Quantity"], horizontal=True)
top_n = st.slider("Number of products", 5, 30, 15)
st.plotly_chart(top_products_chart(clean_df, by=metric_choice, top_n=top_n), use_container_width=True)

st.markdown("<div class='section-header'>🌍 Geographic Revenue</div>", unsafe_allow_html=True)
st.plotly_chart(revenue_by_country_chart(clean_df), use_container_width=True)

if customer_features is not None:
    st.markdown("<div class='section-header'>👥 Customer Distribution</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(purchase_frequency_distribution(customer_features), use_container_width=True)
    with col2:
        st.plotly_chart(repeat_vs_onetime_chart(customer_features), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(customer_spending_distribution(customer_features), use_container_width=True)
    with col2:
        st.plotly_chart(order_value_distribution(customer_features), use_container_width=True)

    # ── Customer Features Table ──────────────────────────────────────────────
    st.markdown("<div class='section-header'>📊 Customer Feature Table</div>", unsafe_allow_html=True)
    st.caption("One row per customer. Download below.")
    st.dataframe(
        customer_features.head(500).style.format({
            "monetary": "£{:,.2f}",
            "avg_order_value": "£{:,.2f}",
            "recency": "{:.0f}d",
            "frequency": "{:.0f}",
        }),
        use_container_width=True,
        hide_index=True,
    )

    csv = customer_features.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Download customer features CSV",
        data=csv,
        file_name="customer_features.csv",
        mime="text/csv",
    )

# ── Country filter ────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🔎 Country Filter</div>", unsafe_allow_html=True)
countries = sorted(clean_df["Country"].unique())
selected = st.multiselect("Filter by country", countries, default=["United Kingdom"])
if selected:
    filtered = clean_df[clean_df["Country"].isin(selected)]
    st.write(f"Showing {len(filtered):,} rows for {selected}")
    st.dataframe(filtered.head(200), use_container_width=True)
