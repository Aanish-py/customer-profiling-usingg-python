"""
pages/5_Churn_Analysis.py
──────────────────────────
Customer churn prediction and analysis page.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import numpy as np
from config import APP_ICON, APP_TITLE

st.set_page_config(page_title=f"Churn Analysis — {APP_TITLE}", page_icon=APP_ICON, layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.section-header { font-size:1.3rem; font-weight:600; border-left:3px solid #4F8EF7;
    padding-left:0.75rem; margin:1.5rem 0 1rem; color:#E6EDF3; }
.info-box { background:rgba(79,142,247,0.07); border:1px solid rgba(79,142,247,0.25);
    border-radius:10px; padding:1rem 1.25rem; margin:1rem 0; font-size:0.9rem; }
.warning-box { background:rgba(210,153,34,0.07); border:1px solid rgba(210,153,34,0.25);
    border-radius:10px; padding:1rem 1.25rem; margin:1rem 0; font-size:0.9rem; }
</style>
""", unsafe_allow_html=True)

st.title("🚨 Churn-Risk Analysis")

if "purchase_df" not in st.session_state or st.session_state["purchase_df"] is None:
    st.warning("Load data first via ⚙️ Settings.")
    st.stop()

purchase_df = st.session_state["purchase_df"]

# ── Configuration ─────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>⚙ Configuration</div>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    churn_window = st.slider(
        "Churn window (days)",
        min_value=30, max_value=365, value=90, step=15,
        help="A customer is churned if they make no purchase within this many days after the cutoff.",
    )
with col2:
    st.markdown("""
    <div class='info-box'>
        <strong>Temporal construction:</strong> Features are built from purchases
        <em>on or before</em> the cutoff date. Labels are derived from purchases
        <em>after</em> the cutoff. Customers whose observation window is incomplete
        are excluded. This prevents data leakage.
    </div>
    """, unsafe_allow_html=True)

if st.button("▶ Train Churn Model", type="primary"):
    from src.churn_prediction import train_churn_model
    with st.spinner("Training churn models…"):
        churn = train_churn_model(purchase_df, churn_window_days=churn_window)
    st.session_state["churn_result"] = churn
    if churn.best_pipeline is not None:
        st.success(
            f"✅ Trained. Best: {churn.best_model_name} | "
            f"RF AUC={churn.rf_auc:.3f} | LR AUC={churn.lr_auc:.3f}"
        )
    else:
        st.warning(churn.notes[-1] if churn.notes else "Insufficient data.")

churn = st.session_state.get("churn_result")
if churn is None:
    st.stop()

if churn.best_pipeline is None:
    st.markdown("<div class='warning-box'>", unsafe_allow_html=True)
    for note in churn.notes:
        st.write(f"⚠ {note}")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📊 Model Performance</div>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Churn Rate", f"{churn.churn_rate:.1%}")
c2.metric("Best Model", churn.best_model_name)

import math
rf_auc = churn.rf_auc if not math.isnan(churn.rf_auc) else None
lr_auc = churn.lr_auc if not math.isnan(churn.lr_auc) else None
c3.metric("Random Forest AUC", f"{rf_auc:.3f}" if rf_auc else "N/A")
c4.metric("Logistic Regression AUC", f"{lr_auc:.3f}" if lr_auc else "N/A")

# ── ROC Curve ─────────────────────────────────────────────────────────────────
from src.visualizations import roc_curve_chart, confusion_matrix_chart, feature_importance_chart, churn_probability_histogram

if len(churn.test_labels) > 0 and len(np.unique(churn.test_labels)) > 1:
    st.markdown("<div class='section-header'>📈 ROC Curves</div>", unsafe_allow_html=True)
    st.plotly_chart(
        roc_curve_chart(
            churn.test_labels,
            churn.lr_predictions if len(churn.lr_predictions) > 0 else churn.best_probas,
            churn.rf_predictions if len(churn.rf_predictions) > 0 else churn.best_probas,
            churn.lr_auc, churn.rf_auc,
        ),
        use_container_width=True,
    )

# ── Confusion matrix ──────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🔷 Confusion Matrix</div>", unsafe_allow_html=True)
if churn.confusion.size > 0:
    st.plotly_chart(
        confusion_matrix_chart(churn.confusion, churn.best_model_name),
        use_container_width=True,
    )

# ── Classification report ─────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📋 Classification Report</div>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    st.subheader("Logistic Regression")
    if churn.lr_report:
        lr_df = pd.DataFrame(churn.lr_report).T.reset_index().rename(columns={"index": "Class"})
        st.dataframe(lr_df.style.format({
            "precision": "{:.3f}", "recall": "{:.3f}", "f1-score": "{:.3f}",
        }), use_container_width=True, hide_index=True)
with col2:
    st.subheader("Random Forest")
    if churn.rf_report:
        rf_df = pd.DataFrame(churn.rf_report).T.reset_index().rename(columns={"index": "Class"})
        st.dataframe(rf_df.style.format({
            "precision": "{:.3f}", "recall": "{:.3f}", "f1-score": "{:.3f}",
        }), use_container_width=True, hide_index=True)

# ── Feature importance ────────────────────────────────────────────────────────
if churn.feature_importances is not None:
    st.markdown("<div class='section-header'>🔍 Feature Importance</div>", unsafe_allow_html=True)
    st.plotly_chart(
        feature_importance_chart(churn.feature_importances, f"Feature Importance — {churn.best_model_name}"),
        use_container_width=True,
    )

# ── Probability distribution ──────────────────────────────────────────────────
if len(churn.best_probas) > 0:
    st.markdown("<div class='section-header'>📊 Churn Probability Distribution</div>", unsafe_allow_html=True)
    st.plotly_chart(churn_probability_histogram(churn.best_probas), use_container_width=True)

# ── Per-customer prediction ───────────────────────────────────────────────────
st.markdown("<div class='section-header'>👤 Predict Churn for a Customer</div>", unsafe_allow_html=True)
customer_features = st.session_state.get("customer_features")
if customer_features is not None:
    cids = sorted(customer_features["CustomerID"].tolist())
    selected_cid = st.selectbox("Select Customer", cids, format_func=lambda x: f"Customer {x}")
    if st.button("Estimate Churn Risk"):
        from src.churn_prediction import predict_churn, churn_risk_category
        proba = predict_churn(int(selected_cid), purchase_df, churn)
        if proba is not None:
            risk = churn_risk_category(proba)
            color = "red" if risk == "High Risk" else ("orange" if risk == "Medium Risk" else "green")
            st.markdown(f"""
            <div style='border:1px solid #{color}; border-radius:10px; padding:1rem;
                        background:rgba(0,0,0,0.2);'>
                <strong>Customer {selected_cid}:</strong> Churn probability = 
                <span style='color:{color}; font-size:1.3rem; font-weight:700;'>{proba:.1%}</span>
                &nbsp;—&nbsp; <strong>{risk}</strong>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Cannot estimate for this customer.")

# ── Batch at-risk table ───────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📋 At-Risk Customer List</div>", unsafe_allow_html=True)
risk_threshold = st.slider("High-risk threshold", 0.4, 0.9, 0.6, 0.05)
if st.button("Generate At-Risk Customer List"):
    from src.churn_prediction import predict_churn, churn_risk_category
    if customer_features is not None:
        rows = []
        for cid in customer_features["CustomerID"].tolist():
            p = predict_churn(int(cid), purchase_df, churn)
            if p is not None:
                rows.append({
                    "CustomerID": cid,
                    "churn_probability": round(p, 4),
                    "risk_category": churn_risk_category(p),
                })
        at_risk_df = pd.DataFrame(rows)
        at_risk_df = at_risk_df[at_risk_df["churn_probability"] >= risk_threshold]
        at_risk_df = at_risk_df.sort_values("churn_probability", ascending=False)
        st.write(f"Found {len(at_risk_df):,} at-risk customers (threshold ≥ {risk_threshold:.0%})")
        st.dataframe(at_risk_df, use_container_width=True, hide_index=True)
        csv = at_risk_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇ Download at-risk CSV", data=csv,
                           file_name="at_risk_customers.csv", mime="text/csv")

# ── Notes ─────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📝 Notes</div>", unsafe_allow_html=True)
for note in churn.notes:
    st.markdown(f"- {note}")
st.markdown(f"""
<div class='warning-box'>
    Churn probabilities are model estimates derived from historical purchase patterns.
    A high probability does not mean a customer <em>will</em> churn — only that they
    share characteristics with customers who have churned historically.
    Use these scores to prioritise retention efforts, not as definitive verdicts.
    Cutoff date used: <strong>{churn.cutoff_date}</strong>.
</div>
""", unsafe_allow_html=True)
