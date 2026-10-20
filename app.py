"""
app.py — Customer Behavior Intelligence System
Main Streamlit entry point (Executive Overview / Home page).
"""

from __future__ import annotations

import sys
import os
import math

# Ensure the project root is in the path so `src` can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from config import (
    APP_ICON,
    APP_TITLE,
    BACKGROUND_COLOR,
    DEFAULT_DATA_FILE,
    PRIMARY_COLOR,
    SECONDARY_BG,
    TEXT_COLOR,
    ACCENT_COLOR,
    SUCCESS_COLOR,
    WARNING_COLOR,
    DANGER_COLOR,
    MUTED_COLOR,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif !important;
    color: {TEXT_COLOR} !important;
}}

.main .block-container {{
    background-color: {BACKGROUND_COLOR};
    padding-top: 1.5rem;
    max-width: 1400px;
}}

section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #0D1117 0%, #161B22 100%);
    border-right: 1px solid #21262D;
}}

section[data-testid="stSidebar"] .block-container {{
    padding-top: 1rem;
}}

.stMetric {{
    background: {SECONDARY_BG};
    border: 1px solid #21262D;
    border-radius: 12px;
    padding: 1rem;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}

.stMetric:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(79, 142, 247, 0.15);
}}

[data-testid="stMetricValue"] {{
    color: {ACCENT_COLOR} !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}}

[data-testid="stMetricLabel"] {{
    color: {MUTED_COLOR} !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

.kpi-card {{
    background: linear-gradient(135deg, {SECONDARY_BG} 0%, #1c2433 100%);
    border: 1px solid #21262D;
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    transition: all 0.25s ease;
}}

.kpi-card:hover {{
    border-color: {PRIMARY_COLOR};
    box-shadow: 0 0 20px rgba(79, 142, 247, 0.1);
}}

.kpi-value {{
    font-size: 2rem;
    font-weight: 700;
    color: {ACCENT_COLOR};
    line-height: 1.2;
}}

.kpi-label {{
    font-size: 0.75rem;
    color: {MUTED_COLOR};
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.25rem;
}}

.section-header {{
    font-size: 1.4rem;
    font-weight: 600;
    color: {TEXT_COLOR};
    border-left: 3px solid {PRIMARY_COLOR};
    padding-left: 0.75rem;
    margin: 1.5rem 0 1rem;
}}

.badge-success {{ background: rgba(63,185,80,0.15); color: {SUCCESS_COLOR}; border: 1px solid rgba(63,185,80,0.3); border-radius: 99px; padding: 0.2rem 0.6rem; font-size: 0.72rem; }}
.badge-warning {{ background: rgba(210,153,34,0.15); color: {WARNING_COLOR}; border: 1px solid rgba(210,153,34,0.3); border-radius: 99px; padding: 0.2rem 0.6rem; font-size: 0.72rem; }}
.badge-danger  {{ background: rgba(248,81,73,0.15);  color: {DANGER_COLOR};  border: 1px solid rgba(248,81,73,0.3); border-radius: 99px; padding: 0.2rem 0.6rem; font-size: 0.72rem; }}
.badge-info    {{ background: rgba(79,142,247,0.15); color: {ACCENT_COLOR};  border: 1px solid rgba(79,142,247,0.3); border-radius: 99px; padding: 0.2rem 0.6rem; font-size: 0.72rem; }}

.info-box {{
    background: rgba(79,142,247,0.07);
    border: 1px solid rgba(79,142,247,0.25);
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin: 1rem 0;
    color: {TEXT_COLOR};
    font-size: 0.9rem;
    line-height: 1.6;
}}

.warning-box {{
    background: rgba(210,153,34,0.07);
    border: 1px solid rgba(210,153,34,0.25);
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin: 1rem 0;
    color: {TEXT_COLOR};
    font-size: 0.9rem;
}}

.hero-gradient {{
    background: linear-gradient(135deg, #0D1117 0%, #111827 50%, #0f1923 100%);
    border: 1px solid #21262D;
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 1.5rem;
}}

div[data-testid="stDataFrame"] {{
    border-radius: 10px;
    overflow: hidden;
}}

.stButton > button {{
    background: linear-gradient(135deg, {PRIMARY_COLOR}, #3a6fd8);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.25rem;
    font-weight: 500;
    transition: all 0.2s ease;
}}

.stButton > button:hover {{
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(79,142,247,0.35);
}}

hr {{
    border-color: #21262D !important;
}}
</style>
""", unsafe_allow_html=True)


# ── Session state helpers ─────────────────────────────────────────────────────

def data_loaded() -> bool:
    return "clean_df" in st.session_state and st.session_state["clean_df"] is not None


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center; padding: 0.5rem 0 1rem;'>
        <div style='font-size:2.2rem;'>{APP_ICON}</div>
        <div style='font-size:1rem; font-weight:700; color:#E6EDF3;'>{APP_TITLE}</div>
        <div style='font-size:0.7rem; color:#8B949E; margin-top:0.2rem;'>
            E-Commerce Intelligence Platform
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    if data_loaded():
        df = st.session_state["clean_df"]
        n_customers = df["CustomerID"].nunique()
        st.markdown(f"""
        <div style='background:rgba(63,185,80,0.1); border:1px solid rgba(63,185,80,0.3);
                    border-radius:8px; padding:0.6rem 0.8rem; margin-bottom:0.5rem;'>
            <span style='color:#3FB950; font-size:0.75rem; font-weight:600;'>
                ✓ Dataset loaded
            </span><br>
            <span style='color:#8B949E; font-size:0.7rem;'>
                {len(df):,} rows · {n_customers:,} customers
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background:rgba(210,153,34,0.1); border:1px solid rgba(210,153,34,0.3);
                    border-radius:8px; padding:0.6rem 0.8rem; margin-bottom:0.5rem;'>
            <span style='color:#D29922; font-size:0.75rem; font-weight:600;'>
                ⚠ No dataset loaded
            </span><br>
            <span style='color:#8B949E; font-size:0.7rem;'>
                Upload via Settings page →
            </span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("**Navigation**")
    st.page_link("app.py", label="🏠 Executive Overview")
    st.page_link("pages/1_Data_Explorer.py", label="🔍 Data Explorer")
    st.page_link("pages/2_Customer_Profiles.py", label="👤 Customer Profiles")
    st.page_link("pages/3_Segmentation.py", label="🎯 Segmentation")
    st.page_link("pages/4_Next_Purchase.py", label="📅 Next Purchase")
    st.page_link("pages/5_Churn_Analysis.py", label="🚨 Churn Analysis")
    st.page_link("pages/6_Recommendations.py", label="💡 Recommendations")
    st.page_link("pages/7_Model_Evaluation.py", label="📊 Model Evaluation")
    st.page_link("pages/8_Settings.py", label="⚙️ Settings")

    st.divider()
    st.markdown(
        "<div style='font-size:0.65rem; color:#8B949E; text-align:center;'>"
        "UCI Online Retail Dataset<br>"
        "All metrics computed from real data"
        "</div>",
        unsafe_allow_html=True,
    )


# ── Main content ──────────────────────────────────────────────────────────────

st.markdown("""
<div class='hero-gradient'>
    <h1 style='font-size:2rem; font-weight:700; margin:0 0 0.5rem;'>
        🧠 Customer Behavior Intelligence
    </h1>
    <p style='color:#8B949E; font-size:1rem; margin:0;'>
        An AI-powered analytics platform for e-commerce customer understanding,
        segmentation, churn detection, and purchase prediction.
    </p>
</div>
""", unsafe_allow_html=True)

if not data_loaded():
    if os.path.exists(DEFAULT_DATA_FILE):
        st.markdown(f"""
        <div style='background:rgba(63,185,80,0.08); border:1px solid rgba(63,185,80,0.3);
                    border-radius:12px; padding:1.25rem 1.5rem; margin-bottom:1.2rem;'>
            <div style='color:#3FB950; font-weight:600; font-size:1.05rem;'>
                📁 Dataset Detected: <code>Online Retail.xlsx</code> ({os.path.getsize(DEFAULT_DATA_FILE) / (1024*1024):.1f} MB)
            </div>
            <div style='color:#8B949E; font-size:0.88rem; margin:0.4rem 0 0.8rem;'>
                The official UCI Online Retail dataset is ready in <code>data/</code>. Click below to load, preprocess, and unlock all modules in one click.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⚡ Quick Load & Initialize Platform", type="primary", use_container_width=True):
            with st.spinner("Loading and processing dataset..."):
                from src.data_loader import load_data
                from src.preprocessing import clean_data, get_purchase_df
                from src.feature_engineering import build_customer_features
                raw_df = load_data(DEFAULT_DATA_FILE)
                clean_df, report = clean_data(raw_df)
                purchase_df = get_purchase_df(clean_df)
                customer_features = build_customer_features(purchase_df)
                st.session_state["raw_df"] = raw_df
                st.session_state["clean_df"] = clean_df
                st.session_state["purchase_df"] = purchase_df
                st.session_state["customer_features"] = customer_features
                st.session_state["preprocessing_report"] = report
                st.rerun()
    else:
        st.markdown("""
        <div class='info-box'>
            <strong>👋 Welcome!</strong> To get started, upload the UCI Online Retail dataset on the
            <strong>⚙️ Settings</strong> page. Once loaded, all analysis modules will activate automatically.
            <br><br>
            <strong>Dataset source:</strong>
            <a href='https://archive.ics.uci.edu/dataset/352/online+retail'
               style='color:#58A6FF;' target='_blank'>
                https://archive.ics.uci.edu/dataset/352/online+retail
            </a>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Platform Modules</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    modules = [
        ("🔍", "Data Explorer", "Inspect raw data, cleaning stats, and quality metrics"),
        ("👤", "Customer Profiles", "Per-customer RFM metrics, order history, and recommendations"),
        ("🎯", "Segmentation", "K-Means clustering with PCA visualisation and segment profiling"),
        ("📅", "Next Purchase", "Predict days until a customer's next purchase"),
        ("🚨", "Churn Analysis", "Identify at-risk customers with probability estimates"),
        ("💡", "Recommendations", "Co-purchase and CF-based product suggestions"),
    ]
    cols_cycle = [col1, col2, col3, col1, col2, col3]
    for col, (icon, name, desc) in zip(cols_cycle, modules):
        with col:
            st.markdown(f"""
            <div class='kpi-card'>
                <div style='font-size:1.5rem;'>{icon}</div>
                <div style='font-weight:600; color:#E6EDF3; margin-top:0.4rem;'>{name}</div>
                <div style='font-size:0.8rem; color:#8B949E; margin-top:0.3rem;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div class='warning-box'>
        <strong>📥 How to get the dataset:</strong><br>
        1. Visit <a href='https://archive.ics.uci.edu/dataset/352/online+retail'
                    style='color:#58A6FF;' target='_blank'>UCI ML Repository</a><br>
        2. Download <code>Online Retail.xlsx</code><br>
        3. Go to ⚙️ Settings → upload the file<br>
        4. The platform will process it and unlock all modules automatically.
    </div>
    """, unsafe_allow_html=True)

else:
    clean_df = st.session_state["clean_df"]
    customer_features = st.session_state.get("customer_features")
    purchase_df = clean_df[~clean_df["is_cancelled"]]

    # ── KPI Cards ──────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>📊 Executive KPIs</div>", unsafe_allow_html=True)

    total_revenue = purchase_df["Revenue"].sum()
    unique_customers = purchase_df["CustomerID"].nunique()
    total_orders = purchase_df["InvoiceNo"].nunique()
    avg_order_val = purchase_df.groupby("InvoiceNo")["Revenue"].sum().mean()
    cancelled_pct = clean_df["is_cancelled"].mean() * 100

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    kpis = [
        (col1, "£{:,.0f}".format(total_revenue), "Total Revenue"),
        (col2, f"{unique_customers:,}", "Unique Customers"),
        (col3, f"{total_orders:,}", "Total Orders"),
        (col4, "£{:,.2f}".format(avg_order_val), "Avg Order Value"),
        (col5, f"{cancelled_pct:.1f}%", "Cancellation Rate"),
        (col6, f"{purchase_df['StockCode'].nunique():,}", "Unique Products"),
    ]
    for col, val, label in kpis:
        with col:
            st.metric(label, val)

    date_min = purchase_df["InvoiceDate"].min().date()
    date_max = purchase_df["InvoiceDate"].max().date()
    st.caption(f"📅 Data period: {date_min} → {date_max}")

    # ── Charts ─────────────────────────────────────────────────────────────
    from src.visualizations import (
        monthly_revenue_chart,
        monthly_orders_chart,
        repeat_vs_onetime_chart,
        revenue_by_country_chart,
    )

    st.markdown("<div class='section-header'>📈 Revenue Overview</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(monthly_revenue_chart(clean_df), use_container_width=True)
    with col2:
        st.plotly_chart(monthly_orders_chart(clean_df), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        if customer_features is not None:
            st.plotly_chart(repeat_vs_onetime_chart(customer_features), use_container_width=True)
        else:
            st.info("Run the Data Explorer to build customer features and see this chart.")
    with col2:
        st.plotly_chart(revenue_by_country_chart(clean_df), use_container_width=True)

    # ── Segment summary ─────────────────────────────────────────────────────
    if st.session_state.get("segmentation_result") is not None and customer_features is not None:
        from src.segmentation import cluster_profile_table
        st.markdown(
            "<div class='section-header'>🎯 Customer Segment Summary</div>",
            unsafe_allow_html=True,
        )
        result = st.session_state["segmentation_result"]
        profile = cluster_profile_table(customer_features, result)
        st.dataframe(profile, use_container_width=True, hide_index=True)

    # ── Churn summary ───────────────────────────────────────────────────────
    churn = st.session_state.get("churn_result")
    if churn is not None and churn.best_pipeline is not None:
        st.markdown(
            "<div class='section-header'>🚨 Churn Risk Summary</div>",
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("Overall Churn Rate", f"{churn.churn_rate:.1%}")
        c2.metric("Best Model", churn.best_model_name)
        best_auc = max(
            x for x in [churn.lr_auc, churn.rf_auc] if not math.isnan(x)
        ) if not (math.isnan(churn.lr_auc) and math.isnan(churn.rf_auc)) else float("nan")
        c3.metric("ROC-AUC", f"{best_auc:.3f}" if not math.isnan(best_auc) else "N/A")
