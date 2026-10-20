"""
pages/7_Model_Evaluation.py
────────────────────────────
Consolidated model evaluation and scientific integrity page.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import numpy as np
import math
from config import APP_ICON, APP_TITLE

st.set_page_config(page_title=f"Model Evaluation — {APP_TITLE}", page_icon=APP_ICON, layout="wide")

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

st.title("📊 Model Evaluation & Scientific Integrity")

st.markdown("""
<div class='info-box'>
    This page summarises all trained models, their evaluation methodology,
    and the measures taken to ensure scientific integrity.
    All metrics are computed on held-out data using chronological splits —
    never on training data.
</div>
""", unsafe_allow_html=True)

# ── Segmentation ──────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🎯 Segmentation (K-Means)</div>", unsafe_allow_html=True)
seg = st.session_state.get("segmentation_result")
if seg:
    c1, c2, c3 = st.columns(3)
    c1.metric("Algorithm", "K-Means")
    c2.metric("K (clusters)", seg.n_clusters)
    c3.metric("Best Silhouette", f"{seg.silhouette_scores.get(seg.n_clusters, 0):.3f}")

    col1, col2 = st.columns(2)
    with col1:
        from src.evaluation import inertia_summary
        st.markdown("**Elbow Method (Inertia by K)**")
        st.dataframe(inertia_summary(seg.inertias), use_container_width=True, hide_index=True)
    with col2:
        from src.evaluation import silhouette_summary
        st.markdown("**Silhouette Score by K**")
        st.dataframe(silhouette_summary(seg.silhouette_scores), use_container_width=True, hide_index=True)

    st.markdown("**Methodology:**")
    st.markdown("""
    - Features: recency, frequency (log), monetary (log), avg_order_value (log), unique_products (log), tenure_days.
    - Skewed features log-transformed before scaling.
    - StandardScaler applied within a sklearn Pipeline (fit on all customers — clustering is unsupervised).
    - K selected by highest silhouette score on sweep of K=2..9.
    - PCA 2-D projection for visualisation only; clustering is done in the original scaled space.
    - Segment names derived from cluster centroid rankings, not predetermined.
    """)
else:
    st.info("No segmentation trained yet. Run it on the 🎯 Segmentation page.")

# ── Next Purchase ─────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📅 Next-Purchase Prediction</div>", unsafe_allow_html=True)
npp = st.session_state.get("next_purchase_result")
if npp and npp.best_pipeline is not None:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Best Model", npp.best_model_name)
    c2.metric("Test MAE", f"{npp.model_mae:.1f} d")
    c3.metric("Test RMSE", f"{npp.model_rmse:.1f} d")
    c4.metric("Baseline MAE", f"{npp.baseline_mae:.1f} d")
    c5.metric("Training Examples", f"{npp.training_samples:,}")

    improvement = (npp.baseline_mae - npp.model_mae) / npp.baseline_mae * 100
    if improvement > 0:
        st.success(f"Model improves over baseline by {improvement:.1f}% on MAE.")
    else:
        st.info(f"Model is {abs(improvement):.1f}% behind baseline — sparse data makes this task difficult.")

    st.markdown("""
    **Methodology:**
    - One training example per (customer, purchase) event (not the last purchase).
    - Features computed from all purchases up to and including the current one.
    - Chronological train (70%) / validation (15%) / test (15%) split.
    - Baseline: predict mean historical inter-order gap.
    - Models compared: Random Forest vs Gradient Boosting; best chosen by validation MAE.
    - No future data leaks into features at any step.
    """)

    for note in npp.notes:
        st.caption(f"ℹ {note}")
elif npp:
    st.warning(npp.notes[-1] if npp.notes else "Model not trained.")
else:
    st.info("Train the model on the 📅 Next Purchase page.")

# ── Churn ─────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🚨 Churn Prediction</div>", unsafe_allow_html=True)
churn = st.session_state.get("churn_result")
if churn and churn.best_pipeline is not None:
    rf_auc = churn.rf_auc if not math.isnan(churn.rf_auc) else None
    lr_auc = churn.lr_auc if not math.isnan(churn.lr_auc) else None
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Best Model", churn.best_model_name)
    c2.metric("Churn Rate", f"{churn.churn_rate:.1%}")
    c3.metric("RF AUC", f"{rf_auc:.3f}" if rf_auc else "N/A")
    c4.metric("LR AUC", f"{lr_auc:.3f}" if lr_auc else "N/A")

    st.markdown("**Classification Reports:**")
    col1, col2 = st.columns(2)
    with col1:
        if churn.lr_report:
            st.caption("Logistic Regression")
            lr_df = pd.DataFrame(churn.lr_report).T
            st.dataframe(lr_df.style.format("{:.3f}"), use_container_width=True)
    with col2:
        if churn.rf_report:
            st.caption("Random Forest")
            rf_df = pd.DataFrame(churn.rf_report).T
            st.dataframe(rf_df.style.format("{:.3f}"), use_container_width=True)

    st.markdown(f"""
    **Methodology:**
    - Cutoff date: `{churn.cutoff_date}` | Churn window: {churn.churn_window_days} days.
    - Features built from purchases ≤ cutoff; labels from purchases after cutoff.
    - Customers with incomplete observation windows excluded.
    - Class imbalance handled with `compute_class_weight('balanced')`.
    - Train (70%) / test (30%) split, chronological on recency.
    - ROC-AUC, precision, recall, F1, confusion matrix reported.
    """)
    for note in churn.notes:
        st.caption(f"ℹ {note}")
elif churn:
    st.warning(churn.notes[-1] if churn.notes else "Churn model disabled.")
else:
    st.info("Train the model on the 🚨 Churn Analysis page.")

# ── Recommendations ───────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>💡 Recommendations</div>", unsafe_allow_html=True)
rec = st.session_state.get("recommender")
rec_eval = st.session_state.get("rec_eval")
if rec and rec_eval:
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Hit Rate@{rec_eval['n']}", f"{rec_eval['hit_rate_at_n']:.3f}")
    c2.metric(f"MRR@{rec_eval['n']}", f"{rec_eval['mrr_at_n']:.3f}")
    c3.metric("Customers Evaluated", f"{rec_eval['evaluated_customers']:,}")
    st.markdown("""
    **Methodology:**
    - Item-item CF: cosine similarity on binary customer-product interaction matrix.
    - Association rules: Apriori with configurable support and confidence thresholds.
    - Popularity fallback for cold-start customers.
    - Offline evaluation: held-out last purchase per customer; hit rate and MRR computed.
    """)
    for note in rec.notes:
        st.caption(f"ℹ {note}")
else:
    st.info("Build the recommender on the 💡 Recommendations page.")

# ── Data leakage statement ────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🛡 Data Leakage Prevention</div>", unsafe_allow_html=True)
st.markdown("""
| Model | Leakage prevention measure |
|-------|---------------------------|
| Segmentation | No temporal leakage — unsupervised; all data is used for clustering |
| Next-purchase | Chronological 70/15/15 split; each example uses only purchases ≤ observation date |
| Churn | Single cutoff date; features from ≤ cutoff, labels from > cutoff; incomplete windows excluded |
| Recommendations | Evaluation uses held-out last purchase; training never sees the held-out item |
| Preprocessing | StandardScaler fitted only on training data within sklearn Pipelines |
""")

st.markdown("""
<div class='info-box'>
    <strong>Reproducibility:</strong> All models use <code>random_state=42</code>.
    Preprocessing steps produce deterministic output given the same input.
    Model results will vary if the dataset changes or preprocessing settings are modified.
</div>
""", unsafe_allow_html=True)
