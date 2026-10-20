"""
pages/4_Next_Purchase.py
─────────────────────────
Next-purchase prediction page.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import numpy as np
from config import APP_ICON, APP_TITLE

st.set_page_config(page_title=f"Next Purchase — {APP_TITLE}", page_icon=APP_ICON, layout="wide")

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

st.title("📅 Next-Purchase Prediction")

if "purchase_df" not in st.session_state or st.session_state["purchase_df"] is None:
    st.warning("Load data first via ⚙️ Settings.")
    st.stop()

purchase_df = st.session_state["purchase_df"]

# ── Train ─────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🚀 Train Model</div>", unsafe_allow_html=True)
st.markdown("""
<div class='info-box'>
    <strong>How it works:</strong> For each customer with ≥ 3 valid purchases,
    we create one training example per purchase event (except the last).
    Features are built from all purchases <em>up to that point</em>; the target is
    the number of days until the <em>next</em> purchase.
    The dataset is split <em>chronologically</em> — no future data leaks into training.
</div>
""", unsafe_allow_html=True)

if st.button("▶ Train Next-Purchase Model", type="primary"):
    from src.next_purchase import train_next_purchase_model
    with st.spinner("Training… (this may take a minute)"):
        result = train_next_purchase_model(purchase_df)
    st.session_state["next_purchase_result"] = result
    if result.best_pipeline is not None:
        st.success(
            f"✅ Model trained: {result.best_model_name} | "
            f"Test MAE = {result.model_mae:.1f} days | "
            f"Baseline MAE = {result.baseline_mae:.1f} days"
        )
    else:
        st.warning(result.notes[-1] if result.notes else "Insufficient data.")

result = st.session_state.get("next_purchase_result")
if result is None:
    st.stop()

if result.best_pipeline is None:
    st.markdown("<div class='warning-box'>", unsafe_allow_html=True)
    for note in result.notes:
        st.write(f"⚠ {note}")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ── Evaluation metrics ────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📊 Model Evaluation</div>", unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Best Model", result.best_model_name)
c2.metric("Test MAE", f"{result.model_mae:.1f} days")
c3.metric("Test RMSE", f"{result.model_rmse:.1f} days")
c4.metric("Baseline MAE", f"{result.baseline_mae:.1f} days")
c5.metric("Training Samples", f"{result.training_samples:,}")

improvement = ((result.baseline_mae - result.model_mae) / result.baseline_mae * 100)
if improvement > 0:
    st.success(f"📈 Model improves over baseline by {improvement:.1f}% (MAE)")
else:
    st.info(f"ℹ Model MAE is {abs(improvement):.1f}% higher than baseline. "
            "The baseline is strong for this dataset — see notes.")

# ── Feature importance ────────────────────────────────────────────────────────
if result.feature_importances is not None:
    st.markdown("<div class='section-header'>🔍 Feature Importance</div>", unsafe_allow_html=True)
    from src.visualizations import feature_importance_chart
    st.plotly_chart(
        feature_importance_chart(result.feature_importances, "Feature Importance — Next-Purchase"),
        use_container_width=True,
    )

# ── Per-customer prediction ───────────────────────────────────────────────────
st.markdown("<div class='section-header'>👤 Predict for a Customer</div>", unsafe_allow_html=True)
customer_features = st.session_state.get("customer_features")
if customer_features is not None:
    cids = sorted(customer_features["CustomerID"].tolist())
    selected_cid = st.selectbox("Select Customer ID", cids, format_func=lambda x: f"Customer {x}")
    if st.button("Predict", use_container_width=True):
        from src.next_purchase import predict_next_purchase
        days = predict_next_purchase(int(selected_cid), purchase_df, result)
        if days is not None:
            st.success(f"🛍 Customer {selected_cid}: estimated next purchase in ~**{days:.0f} days**")
        else:
            st.warning(f"Cannot predict for Customer {selected_cid} — insufficient purchase history.")

# ── Batch predictions ─────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📋 Batch Predictions</div>", unsafe_allow_html=True)
if st.button("Generate predictions for all customers"):
    from src.next_purchase import predict_next_purchase
    rows = []
    if customer_features is not None:
        for cid in customer_features["CustomerID"].tolist():
            days = predict_next_purchase(int(cid), purchase_df, result)
            rows.append({"CustomerID": cid, "predicted_days_to_next_purchase": days})
        preds_df = pd.DataFrame(rows)
        st.session_state["next_purchase_preds"] = preds_df
        st.dataframe(preds_df.dropna(), use_container_width=True, hide_index=True)
        csv = preds_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇ Download predictions CSV", data=csv,
                           file_name="next_purchase_predictions.csv", mime="text/csv")

# ── Notes ─────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📝 Notes & Limitations</div>", unsafe_allow_html=True)
for note in result.notes:
    st.markdown(f"- {note}")
st.markdown("""
<div class='warning-box'>
    Next-purchase predictions are order-of-magnitude estimates derived from purchase
    patterns. They should not be used as precise forecasts. E-commerce purchase timing
    is influenced by many factors not present in transaction logs (promotions, seasonality,
    personal circumstances). Interpret predictions as directional guidance only.
</div>
""", unsafe_allow_html=True)
