# Customer Behavior Intelligence & Next-Purchase Prediction System

> An AI-powered e-commerce analytics platform that profiles customers, segments them with K-Means,
> predicts next purchase timing, estimates churn risk, and recommends products — all from real
> transaction data with no hardcoded metrics.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Dataset](#dataset)
4. [Installation](#installation)
5. [Running the Application](#running-the-application)
6. [Project Structure](#project-structure)
7. [Machine Learning Algorithms](#machine-learning-algorithms)
8. [Feature Definitions](#feature-definitions)
9. [Model Evaluation Methodology](#model-evaluation-methodology)
10. [Data Leakage Prevention](#data-leakage-prevention)
11. [Limitations](#limitations)
12. [Running Tests](#running-tests)
13. [Future Enhancements](#future-enhancements)

---

## Project Overview

This system analyses e-commerce transaction records to:

- Build rich per-customer profiles (RFM + extended features)
- Segment customers automatically using K-Means clustering
- Predict when each customer is likely to make their next purchase
- Estimate the probability that a customer has churned
- Recommend products based on co-purchase patterns and collaborative filtering
- Present everything in a polished Streamlit dashboard

---

## Features

| Module | Description |
|--------|-------------|
| **Data Explorer** | Raw data preview, cleaning report, EDA charts |
| **Customer Profiles** | Per-customer metrics, orders, top products, segment, churn risk, recommendations |
| **Segmentation** | K-Means with elbow/silhouette selection, PCA visualisation, segment profiles |
| **Next Purchase** | Regression model predicting days to next purchase, baseline comparison |
| **Churn Analysis** | Binary classifier, ROC curves, confusion matrix, at-risk customer list |
| **Recommendations** | Item-item CF + association rules + popularity fallback, hit-rate evaluation |
| **Model Evaluation** | Consolidated metrics, methodology, and leakage prevention summary |
| **Settings** | Dataset upload, preprocessing config, one-click model training |

---

## Dataset

**UCI Online Retail Dataset**

- URL: https://archive.ics.uci.edu/dataset/352/online+retail
- File: `Online Retail.xlsx` (~24 MB)
- Records: ~541,909 transactions, Dec 2010 – Dec 2011
- Fields: InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country

### Download Instructions

1. Visit the UCI URL above and click **Download**.
2. Extract the archive to get `Online Retail.xlsx`.
3. **Option A:** Place it in the `data/` folder of this project.
4. **Option B:** Upload it directly via the ⚙️ Settings page in the app.

---

## Installation

### Prerequisites

- Python 3.11 (or 3.10+)
- pip

### Windows

```powershell
cd customer-behavior-intelligence
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### macOS / Linux

```bash
cd customer-behavior-intelligence
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Running the Application

```powershell
# Windows
streamlit run app.py

# macOS / Linux
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

**First-time workflow:**
1. Go to ⚙️ Settings
2. Upload `Online Retail.xlsx` or click "Load from data/ folder"
3. Adjust preprocessing options if desired and click **Load Data & Run Preprocessing**
4. Click **Train All Models** to train segmentation, churn, next-purchase, and the recommender
5. Explore all pages

---

## Project Structure

```
customer-behavior-intelligence/
│
├── app.py                    # Executive overview (Streamlit home page)
├── config.py                 # All tunable parameters and constants
├── requirements.txt
├── README.md
│
├── data/
│   └── README.md             # Dataset download instructions
│
├── models/
│   └── .gitkeep              # Trained models saved here (joblib)
│
├── src/
│   ├── __init__.py
│   ├── data_loader.py        # File loading, column validation
│   ├── preprocessing.py      # Cleaning pipeline with detailed reporting
│   ├── feature_engineering.py # RFM+ customer features
│   ├── customer_profiling.py  # Per-customer profile views
│   ├── segmentation.py       # K-Means + PCA + naming
│   ├── next_purchase.py      # Regression for days-to-next-purchase
│   ├── churn_prediction.py   # Binary churn classifier
│   ├── recommendations.py    # Hybrid recommender
│   ├── evaluation.py         # Shared metric utilities
│   └── visualizations.py    # Plotly chart builders
│
├── pages/
│   ├── 1_Data_Explorer.py
│   ├── 2_Customer_Profiles.py
│   ├── 3_Segmentation.py
│   ├── 4_Next_Purchase.py
│   ├── 5_Churn_Analysis.py
│   ├── 6_Recommendations.py
│   ├── 7_Model_Evaluation.py
│   └── 8_Settings.py
│
└── tests/
    ├── test_preprocessing.py
    ├── test_customer_features.py
    └── test_temporal_splits.py
```

---

## Machine Learning Algorithms

### Segmentation
- **Algorithm:** K-Means (scikit-learn)
- **K selection:** Silhouette score sweep over K=2..9
- **Preprocessing:** StandardScaler within sklearn Pipeline; log1p on skewed features
- **Visualisation:** PCA 2-D projection

### Next-Purchase Prediction
- **Task:** Regression — predict days until next purchase
- **Baseline:** Mean historical inter-order gap per customer
- **Models:** Random Forest Regressor vs Gradient Boosting Regressor
- **Selection:** Best validation MAE wins
- **Split:** Chronological 70/15/15

### Churn Prediction
- **Task:** Binary classification — will a customer purchase again within N days?
- **Models:** Logistic Regression vs Random Forest Classifier
- **Selection:** Best ROC-AUC wins
- **Split:** Chronological; single cutoff date construction
- **Imbalance:** `class_weight='balanced'`

### Recommendations
- **Item-item CF:** Cosine similarity on binary customer-product matrix
- **Association rules:** Apriori (mlxtend) with configurable support/confidence
- **Fallback:** Global popularity ranking
- **Evaluation:** Hit Rate@N and MRR@N on held-out last purchases

---

## Feature Definitions

| Feature | Definition |
|---------|-----------|
| `recency` | Days from last purchase to reference date (lower = more recent) |
| `frequency` | Count of distinct valid (non-cancelled) invoice numbers |
| `monetary` | Net spend: sum of Revenue for valid purchases |
| `avg_order_value` | `monetary / frequency` |
| `avg_qty_per_order` | Mean quantity per invoice |
| `unique_products` | Count of distinct StockCode values |
| `tenure_days` | Days between first and last purchase |
| `repeat_rate` | 1 if frequency > 1, else 0 |
| `inter_order_days` | Mean days between consecutive purchases (NaN for 1-purchase customers) |

**Revenue rule:** `Quantity × UnitPrice`. Cancelled invoices (InvoiceNo starts with 'C') are flagged and excluded from purchase features but retained for net-revenue analysis. Lines with zero/negative price and non-cancelled lines with negative quantity are treated as data errors and removed.

---

## Model Evaluation Methodology

| Model | Training data | Validation | Test | Metric |
|-------|--------------|------------|------|--------|
| Segmentation | All customers | Silhouette on full set | — | Silhouette score |
| Next-purchase | Chron. first 70% | Middle 15% (MAE) | Last 15% | MAE, RMSE vs baseline |
| Churn | Chron. first 70% | — | Last 30% | ROC-AUC, F1, precision/recall |
| Recommendations | All history | — | Held-out last purchase | Hit Rate@N, MRR@N |

---

## Data Leakage Prevention

1. **Preprocessing:** `StandardScaler` fitted inside sklearn `Pipeline` — fit on training data only.
2. **Next-purchase:** Each training example uses only purchases up to the observation date. The target is strictly from the future.
3. **Churn:** Feature cutoff date ≤ label observation date. Customers whose future window extends past the dataset end are excluded.
4. **Recommendations:** Evaluation uses a held-out last purchase that is removed from the training interaction matrix.

---

## Limitations

- The dataset covers 13 months — seasonal patterns may not generalise to other periods.
- ~25% of rows have no CustomerID and are excluded (cannot be attributed to a customer).
- Cancellations (~2% of invoices) are handled carefully but return fraud is not modelled.
- Next-purchase timing is inherently noisy — treat predictions as order-of-magnitude estimates.
- The churn model is trained on a single cutoff date; multiple-cutoff approaches would be more robust.
- Association-rule mining can be slow on the full dataset without filtering.
- Recommendations for very sparse customers rely heavily on the popularity fallback.

---

## Running Tests

```powershell
# Windows
cd customer-behavior-intelligence
python -m pytest tests/ -v

# macOS / Linux
python -m pytest tests/ -v
```

Tests run without downloading the real dataset — all use synthetic minimal DataFrames.

---

## Future Enhancements

- Multi-cutoff churn training for more robust model evaluation
- LSTM / temporal model for next-purchase timing using full sequence history
- Neural collaborative filtering for recommendations
- A/B test simulation for promotion targeting by segment
- Automated model retraining pipeline with scheduled jobs
- Integration with real-time purchase event streams (Kafka / Redis)
- Geographic visualisation with Plotly choropleth maps
- Export trained models via REST API (FastAPI)
