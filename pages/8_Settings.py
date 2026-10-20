"""
pages/8_Settings.py
────────────────────
Dataset upload, preprocessing configuration, and model training triggers.
This is the entry point; users upload their data here before exploring.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
from config import APP_ICON, APP_TITLE, DEFAULT_DATA_FILE

st.set_page_config(page_title=f"Settings — {APP_TITLE}", page_icon=APP_ICON, layout="wide")

# shared CSS snippet
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.section-header { font-size:1.3rem; font-weight:600; border-left:3px solid #4F8EF7;
    padding-left:0.75rem; margin:1.5rem 0 1rem; color:#E6EDF3; }
.info-box { background:rgba(79,142,247,0.07); border:1px solid rgba(79,142,247,0.25);
    border-radius:10px; padding:1rem 1.25rem; margin:1rem 0; font-size:0.9rem; line-height:1.6; }
.warning-box { background:rgba(210,153,34,0.07); border:1px solid rgba(210,153,34,0.25);
    border-radius:10px; padding:1rem 1.25rem; margin:1rem 0; font-size:0.9rem; }
</style>
""", unsafe_allow_html=True)

st.title("⚙️ Settings & Data Loading")

# ── Dataset upload ────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📁 Dataset</div>", unsafe_allow_html=True)

st.markdown("""
<div class='info-box'>
    <strong>UCI Online Retail Dataset</strong><br>
    Download from:
    <a href='https://archive.ics.uci.edu/dataset/352/online+retail'
       style='color:#58A6FF;' target='_blank'>
        https://archive.ics.uci.edu/dataset/352/online+retail
    </a><br>
    The file is named <code>Online Retail.xlsx</code> (~24 MB).
    Upload it below, or place it in the <code>data/</code> folder and click
    "Load from disk".
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])
with col1:
    uploaded_file = st.file_uploader(
        "Upload dataset (Excel or CSV)",
        type=["xlsx", "xls", "csv"],
        help="Upload the UCI Online Retail file or any compatible dataset with the same columns.",
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    file_exists = os.path.exists(DEFAULT_DATA_FILE)
    if file_exists:
        file_size_mb = os.path.getsize(DEFAULT_DATA_FILE) / (1024 * 1024)
        st.markdown(f"<div style='color:#3FB950; font-size:0.8rem; margin-bottom:0.3rem;'>✓ Found in data/ ({file_size_mb:.1f} MB)</div>", unsafe_allow_html=True)
    load_from_disk = st.button("📂 Load from data/ folder", use_container_width=True)
    if not file_exists:
        if st.button("⬇ Download UCI Dataset", use_container_width=True):
            with st.spinner("Downloading from UCI repository (~24 MB)..."):
                import urllib.request
                url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx"
                os.makedirs(os.path.dirname(DEFAULT_DATA_FILE), exist_ok=True)
                urllib.request.urlretrieve(url, DEFAULT_DATA_FILE)
                st.success("Downloaded! Click 'Load from data/ folder' below.")
                st.rerun()

# ── Preprocessing options ─────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🔧 Preprocessing Options</div>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    drop_missing_cid = st.checkbox(
        "Drop rows with missing CustomerID",
        value=True,
        help="Recommended: rows without CustomerID cannot be attributed to a customer.",
    )
    remove_zero_price = st.checkbox(
        "Remove rows with price < £0.01",
        value=True,
        help="Zero/negative prices usually indicate test records or data errors.",
    )
with col2:
    keep_cancelled = st.checkbox(
        "Keep cancelled invoices (flagged, not removed)",
        value=True,
        help="Cancellations are retained with a flag so net-revenue can be computed.",
    )
    nrows = st.number_input(
        "Max rows to load (0 = all)",
        min_value=0, max_value=2_000_000, value=0, step=10_000,
        help="Load a subset for faster iteration during development.",
    )

# ── Load / Process ────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🚀 Load & Process</div>", unsafe_allow_html=True)

run_btn = st.button("▶ Load Data & Run Preprocessing", type="primary", use_container_width=True)

if run_btn or load_from_disk or uploaded_file is not None:
    from src.data_loader import load_data, load_from_upload
    from src.preprocessing import clean_data, get_purchase_df
    from src.feature_engineering import build_customer_features

    try:
        with st.spinner("Loading dataset…"):
            if uploaded_file is not None:
                raw_df = load_from_upload(uploaded_file)
                st.success(f"Uploaded file loaded: {len(raw_df):,} rows.")
            else:
                nrows_arg = int(nrows) if nrows > 0 else None
                raw_df = load_data(DEFAULT_DATA_FILE, nrows=nrows_arg)
                st.success(f"Loaded from disk: {len(raw_df):,} rows.")

        with st.spinner("Cleaning data…"):
            clean_df, report = clean_data(
                raw_df,
                drop_missing_customer=drop_missing_cid,
                remove_zero_price=remove_zero_price,
                keep_cancelled=keep_cancelled,
            )

        with st.spinner("Building customer features…"):
            purchase_df = get_purchase_df(clean_df)
            customer_features = build_customer_features(purchase_df)

        # Persist to session state
        st.session_state["raw_df"] = raw_df
        st.session_state["clean_df"] = clean_df
        st.session_state["purchase_df"] = purchase_df
        st.session_state["customer_features"] = customer_features
        st.session_state["preprocessing_report"] = report

        # Clear previously trained models so they are re-trained on new data
        for key in ["segmentation_result", "churn_result", "next_purchase_result",
                    "recommender", "rec_eval"]:
            st.session_state.pop(key, None)

        st.success(
            f"✅ Done! {report.final_rows:,} clean rows · "
            f"{report.unique_customers:,} customers · "
            f"date range {report.date_range_start} → {report.date_range_end}"
        )

        st.markdown("<div class='section-header'>📋 Preprocessing Report</div>", unsafe_allow_html=True)
        st.dataframe(report.summary_df(), use_container_width=True, hide_index=True)

    except FileNotFoundError as e:
        st.error(str(e))
        st.markdown("""
        <div class='warning-box'>
            <strong>Dataset not found.</strong><br>
            Please upload the file using the uploader above, or download it from the UCI link.
        </div>
        """, unsafe_allow_html=True)
    except ValueError as e:
        st.error(f"Data validation error: {e}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        st.exception(e)

# ── Model training ────────────────────────────────────────────────────────────
if "clean_df" in st.session_state and st.session_state["clean_df"] is not None:
    st.markdown("<div class='section-header'>🤖 Train ML Models</div>", unsafe_allow_html=True)
    st.caption("Train all models at once, or visit individual pages to train them there.")

    col1, col2 = st.columns(2)
    with col1:
        churn_window = st.slider(
            "Churn window (days)",
            min_value=30, max_value=365, value=90, step=30,
            help="A customer is considered churned if they make no purchase within this window.",
        )
    with col2:
        n_clusters = st.slider(
            "Segmentation clusters (K)",
            min_value=2, max_value=9, value=0,
            help="0 = auto-select via silhouette score.",
        )

    if st.button("🔬 Train All Models", type="primary", use_container_width=True):
        from src.segmentation import train_segmentation
        from src.churn_prediction import train_churn_model
        from src.next_purchase import train_next_purchase_model
        from src.recommendations import build_recommender, evaluate_recommendations

        purchase_df = st.session_state["purchase_df"]
        customer_features = st.session_state["customer_features"]

        with st.spinner("Training segmentation…"):
            k = int(n_clusters) if n_clusters > 0 else None
            seg = train_segmentation(customer_features, n_clusters=k)
            st.session_state["segmentation_result"] = seg
        st.success(f"✅ Segmentation: {seg.n_clusters} clusters")

        with st.spinner("Training churn model…"):
            churn = train_churn_model(purchase_df, churn_window_days=churn_window)
            st.session_state["churn_result"] = churn
        if churn.best_pipeline is not None:
            st.success(f"✅ Churn ({churn.best_model_name}): AUC = {max(churn.lr_auc, churn.rf_auc):.3f}")
        else:
            st.warning(f"⚠ Churn model: {churn.notes[-1] if churn.notes else 'insufficient data'}")

        with st.spinner("Training next-purchase model…"):
            npp = train_next_purchase_model(purchase_df)
            st.session_state["next_purchase_result"] = npp
        if npp.best_pipeline is not None:
            st.success(f"✅ Next-purchase ({npp.best_model_name}): MAE = {npp.model_mae:.1f} days")
        else:
            st.warning(f"⚠ Next-purchase: {npp.notes[-1] if npp.notes else 'insufficient data'}")

        with st.spinner("Building recommender…"):
            rec = build_recommender(purchase_df)
            st.session_state["recommender"] = rec
            rec_eval = evaluate_recommendations(purchase_df, rec)
            st.session_state["rec_eval"] = rec_eval
        st.success(f"✅ Recommender built. Hit Rate@10 = {rec_eval['hit_rate_at_n']:.3f}, MRR@10 = {rec_eval['mrr_at_n']:.3f}")

        st.balloons()
        st.markdown("""
        <div class='info-box'>
            All models trained. Navigate to individual pages to explore results.
        </div>
        """, unsafe_allow_html=True)
