"""
pages/3_Segmentation.py
────────────────────────
K-Means customer segmentation page.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import numpy as np
from config import APP_ICON, APP_TITLE

st.set_page_config(page_title=f"Segmentation — {APP_TITLE}", page_icon=APP_ICON, layout="wide")

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

st.title("🎯 Customer Segmentation")

if "customer_features" not in st.session_state or st.session_state["customer_features"] is None:
    st.warning("Load data first via ⚙️ Settings.")
    st.stop()

customer_features = st.session_state["customer_features"]

# ── Training controls ─────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>⚙ Configuration</div>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    k_choice = st.slider("Number of clusters K (0 = auto)", 0, 9, 0)
with col2:
    st.markdown("""
    <div class='info-box'>
        <strong>Auto-select (K=0):</strong> The system evaluates K from 2–9 using the
        <em>silhouette score</em> and picks the K with the best score.
        You can override this by setting K manually.
    </div>
    """, unsafe_allow_html=True)

if st.button("🚀 Run Segmentation", type="primary"):
    from src.segmentation import train_segmentation
    k = int(k_choice) if k_choice > 0 else None
    with st.spinner("Training K-Means…"):
        result = train_segmentation(customer_features, n_clusters=k)
    st.session_state["segmentation_result"] = result
    st.success(f"✅ Segmentation complete: K={result.n_clusters}, "
               f"Silhouette={result.silhouette_scores.get(result.n_clusters, 0):.3f}")

# ── Results ───────────────────────────────────────────────────────────────────
result = st.session_state.get("segmentation_result")
if result is None:
    st.info("Run segmentation above to see results.")
    st.stop()

from src.segmentation import cluster_profile_table, assign_segments
from src.visualizations import cluster_scatter, elbow_chart, silhouette_chart
from src.evaluation import silhouette_summary, inertia_summary

# KPIs
c1, c2, c3 = st.columns(3)
c1.metric("Clusters", result.n_clusters)
c2.metric("Silhouette Score", f"{result.silhouette_scores.get(result.n_clusters, 0):.3f}")
c3.metric("Customers Segmented", f"{len(result.labels):,}")

# ── K selection charts ────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📊 K Selection Analysis</div>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(elbow_chart(result.inertias), use_container_width=True)
with col2:
    st.plotly_chart(silhouette_chart(result.silhouette_scores), use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    st.dataframe(inertia_summary(result.inertias), use_container_width=True, hide_index=True)
with col2:
    st.dataframe(silhouette_summary(result.silhouette_scores), use_container_width=True, hide_index=True)

# ── PCA scatter ───────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🌐 Cluster Visualisation (PCA 2-D)</div>", unsafe_allow_html=True)
st.plotly_chart(cluster_scatter(result.pca_coords, result.labels, result.segment_names), use_container_width=True)

# ── Cluster profile table ─────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📋 Segment Profiles</div>", unsafe_allow_html=True)
profile = cluster_profile_table(customer_features, result)
st.dataframe(
    profile.style.format({
        "recency": "{:.1f} days",
        "frequency": "{:.1f}",
        "monetary": "£{:,.0f}",
        "avg_order_value": "£{:,.0f}",
        "tenure_days": "{:.0f} days",
        "customer_count": "{:,.0f}",
    }),
    use_container_width=True,
    hide_index=True,
)

# ── Segment assignment table ──────────────────────────────────────────────────
st.markdown("<div class='section-header'>👥 Customer Assignments</div>", unsafe_allow_html=True)
seg_df = assign_segments(customer_features, result)
show_cols = ["CustomerID", "recency", "frequency", "monetary", "cluster", "segment"]
show_cols = [c for c in show_cols if c in seg_df.columns]

# Filter by segment
segments = seg_df["segment"].unique().tolist()
selected_seg = st.multiselect("Filter by segment", segments, default=segments)
filtered = seg_df[seg_df["segment"].isin(selected_seg)][show_cols]

st.dataframe(
    filtered.style.format({"recency": "{:.0f}", "frequency": "{:.0f}", "monetary": "£{:,.0f}"}),
    use_container_width=True,
    hide_index=True,
)

csv = seg_df.to_csv(index=False).encode("utf-8")
st.download_button("⬇ Download segmentation CSV", data=csv,
                   file_name="customer_segments.csv", mime="text/csv")

st.markdown("""
<div class='info-box'>
    <strong>Segment names</strong> are assigned automatically by ranking clusters on recency,
    frequency, and monetary value. They reflect the data — not predetermined categories.
    Actual cluster characteristics may vary with different datasets or K values.
</div>
""", unsafe_allow_html=True)
