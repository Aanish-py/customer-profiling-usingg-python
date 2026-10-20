# 📊 Customer Behavior Intelligence & Next-Purchase Prediction System
## Comprehensive Project Report & Business Capabilities Guide

---

## 🎯 Executive Overview

The **Customer Behavior Intelligence & Next-Purchase Prediction System** is an enterprise-ready analytics and machine learning platform engineered to transform raw transactional data into high-value customer understanding and forward-looking business actions.

Rather than looking backward with descriptive dashboards (e.g. "how much revenue was made last quarter"), this platform pairs **exploratory data science** with **predictive AI models** to answer critical business questions:
1. **Who are our best customers, and what defines their buying patterns?** (Unsupervised K-Means Clustering)
2. **When is a customer due to buy again?** (Chronological Regression Models)
3. **Who is slipping away and at immediate risk of churning?** (Supervised Classification with ROC-AUC validation)
4. **What products should we recommend to each individual buyer?** (Item-Item Collaborative Filtering + Association Rules)
5. **Are these models genuinely learning or just predicting noise?** (Strict Out-of-Time Splits & Baseline Benchmarking)

---

## 💡 What the User / Business Achieves From This Project

### 1. Direct Return on Investment (ROI) & Revenue Growth
* **Precision Replenishment Campaigns**: Instead of spamming all customers with weekly newsletters, marketing teams can trigger email/SMS reminders exactly when a customer's individual inter-order gap is due.
* **Higher Basket Size via Cross-Selling**: Association rules identify high-confidence item affinities (e.g. Antecedent: *Tea Caddy* $\to$ Consequent: *Ceramic Teapot*, Lift > 2.5), enabling smart product bundles and checkout suggestions.
* **Proactive Churn Mitigation**: Identifies at-risk customers *before* they are permanently lost. Offering a timely 10% re-activation incentive to the top 10% highest-churn-risk buyers directly preserves recurring customer lifetime value.

### 2. Marketing Efficiency & Cost Reduction
* **Zero Ad Spend Waste**: Stop spending acquisition budget on one-off coupon hunters. Focus retention budgets on high-LTV clusters identified in the Segmentation module.
* **Automated Customer 360**: Customer support and sales reps can look up any `CustomerID` in seconds and see past order history, churn risk score, predicted next purchase date, and personalized recommendations.

### 3. Scientific Integrity & No Data Leakage
* **Proven Model Lift**: Every model is benchmarked against a Dummy Regressor / Dummy Classifier. You never have to guess whether an ML model provides actual statistical advantage over simple historical averages.
* **Chronological Guardrails**: Future transaction information never bleeds into training features. Observation windows are strictly separated from prediction windows.

---

## 🧩 Comprehensive Feature Catalog by Module

```
Interactive Multi-Page Application Layout
├── 🏠 app.py (Executive Overview)
│   ├── Real-time KPI summary ribbon (Revenue, AOV, Orders, Returns)
│   ├── Macro trend charts (Monthly revenue, orders, geography)
│   └── 1-Click Platform Initializer
│
├── 🔍 1_Data_Explorer.py
│   ├── Step-by-step cleaning audit funnel
│   ├── Distribution histograms (Prices, quantities, transaction sizes)
│   └── Exportable customer feature matrix
│
├── 👤 2_Customer_Profiles.py
│   ├── Single-customer lookup (RFM percentiles & lifetime value)
│   ├── Historical purchase timeline & product affinities
│   └── Live predictive card: Next-purchase date, Churn score, Recommendations
│
├── 🎯 3_Segmentation.py
│   ├── Automated K-selection via Silhouette Score & Elbow Curve
│   ├── PCA 2D interactive projection of clusters
│   └── Persona profile table with segment attribute breakdowns
│
├── 📅 4_Next_Purchase.py
│   ├── Ridge Regression vs. Random Forest vs. Dummy Baseline
│   ├── Evaluation metrics (MAE, RMSE, R²)
│   ├── Feature importance rankings
│   └── Individual prediction widget & batch CSV export
│
├── 🚨 5_Churn_Analysis.py
│   ├── Logistic Regression vs. Random Forest Classifier
│   ├── ROC curves, Confusion Matrix, and threshold adjuster
│   └── Downloadable high-risk customer target list
│
├── 💡 6_Recommendations.py
│   ├── Item-Item Collaborative Filtering (Cosine similarity)
│   ├── Association Rule Mining (Support, Confidence, Lift)
│   ├── Cold-start popularity fallback for new customers
│   └── Offline validation: Hit Rate@10 & Mean Reciprocal Rank (MRR@10)
│
├── 📊 7_Model_Evaluation.py
│   ├── Cross-model scorecard & methodology audit
│   └── Data leakage prevention documentation
│
└── ⚙️ 8_Settings.py
    ├── Dataset upload & 1-click download from UCI repository
    ├── Preprocessing parameter controls
    └── 1-Click model training orchestrator
```

---

## 🔬 Machine Learning Specifications & Technical Stack

| Objective | Problem Formulation | Algorithms Implemented | Validation & Metrics | Baseline Comparison |
| :--- | :--- | :--- | :--- | :--- |
| **Segmentation** | Unsupervised Pattern Discovery | K-Means + PCA (Principal Component Analysis) | Silhouette Score, Inertia Elbow | Multi-K evaluation ($K=2 \dots 9$) |
| **Next-Purchase** | Supervised Continuous Regression | Ridge Regression, Random Forest Regressor | Chronological Split, MAE, RMSE, $R^2$ | Dummy Regressor (Mean/Median) |
| **Churn Risk** | Supervised Binary Classification | Logistic Regression, Random Forest Classifier | Out-of-Time Cutoff, ROC-AUC, Precision, Recall, F1 | Dummy Classifier (Stratified/Majority) |
| **Product Recommendations** | Hybrid Collaborative / Association | Item-Item Cosine Similarity + Apriori Rules | Leave-one-out Hit Rate@10, MRR@10 | Global Popularity Fallback |

---

## 📈 Stakeholder Outcomes Matrix

| User Role | Everyday Question Answered | Platform Feature Used | Concrete Business Outcome |
| :--- | :--- | :--- | :--- |
| **Chief Commercial Officer** | *"Is our customer base expanding or stalling?"* | Executive Overview (`app.py`) | Tracks macro net revenue, cancel rate, and repeat vs. one-time buyer proportions. |
| **CRM / Campaign Manager** | *"Which customers need an email today?"* | Next Purchase (`4_Next_Purchase.py`) | Exports batch predictions of customers whose expected repurchase window is within 7 days. |
| **Customer Retention Lead** | *"Who are we about to lose that spends heavily?"* | Churn Analysis (`5_Churn_Analysis.py`) | Filters at-risk customers with high monetary spend for targeted concierge outreach. |
| **E-Commerce Merchandiser** | *"What products should we bundle together?"* | Recommendations (`6_Recommendations.py`) | Leverages high-lift co-purchase rules to build bundle discounts on product pages. |
| **Lead Data Scientist** | *"Is this ML model robust and statistically sound?"* | Model Evaluation (`7_Model_Evaluation.py`) | Inspects out-of-time test scores, MAE reduction over baseline, and feature importances. |

---

## 🛠️ Step-by-Step Workflow Guide

1. **Launch the Application**:
   ```powershell
   python -m streamlit run app.py
   ```
2. **Access Dashboard**: Open `http://localhost:8501` in your browser.
3. **Initialize Data**:
   * Click the **"⚡ Quick Load & Initialize Platform"** button on the home page.
   * Or navigate to **⚙️ Settings** to adjust preprocessing parameters (minimum price, cancellation flags, churn horizons) and click **"🔬 Train All Models"**.
4. **Explore & Act**:
   * Inspect cluster distributions in **🎯 Segmentation**.
   * Run individualized predictions in **📅 Next Purchase** and **🚨 Churn Analysis**.
   * Generate cross-sell rules in **💡 Recommendations**.
   * Download actionable CSV lists for marketing automation.

---

## 🧪 Testing & Verification Summary

The platform includes a dedicated unit test suite in `tests/` covering:
* Data preprocessing filters, cancellation flag preservation, and return handling.
* Edge cases in feature calculations (single order vs. multi-order buyers, zero recency, extreme values).
* Temporal sequence isolation ensuring future events never leak into historical training sets.
* Segmentation consistency and recommendation fallbacks for new users.

**Test execution result**: `36 passed in 8.52s (100% pass rate)`.
