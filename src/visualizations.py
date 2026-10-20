"""
src/visualizations.py
─────────────────────
Reusable Plotly chart builders for all dashboard pages.
All functions return a plotly Figure object ready to pass to st.plotly_chart.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff

# ── Design tokens (match config.py colours) ───────────────────────────────────
BG = "#0D1117"
PAPER_BG = "#161B22"
GRID_COLOR = "#21262D"
FONT_COLOR = "#E6EDF3"
MUTED = "#8B949E"
PRIMARY = "#4F8EF7"
SUCCESS = "#3FB950"
WARNING = "#D29922"
DANGER = "#F85149"
ACCENT = "#58A6FF"
PALETTE = [
    "#4F8EF7", "#3FB950", "#D29922", "#F85149", "#58A6FF",
    "#BC8CFF", "#79C0FF", "#56D364", "#FFA657", "#FF7B72",
]

LAYOUT_DEFAULTS = dict(
    paper_bgcolor=PAPER_BG,
    plot_bgcolor=BG,
    font_color=FONT_COLOR,
    font_family="Inter, Arial, sans-serif",
    xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    margin=dict(l=50, r=30, t=50, b=50),
    legend=dict(
        bgcolor=PAPER_BG,
        bordercolor=GRID_COLOR,
        font_color=FONT_COLOR,
    ),
)


def _apply_layout(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(title=dict(text=title, font_color=FONT_COLOR), **LAYOUT_DEFAULTS)
    return fig


# ── EDA Charts ────────────────────────────────────────────────────────────────

def monthly_revenue_chart(clean_df: pd.DataFrame) -> go.Figure:
    """Line chart of monthly revenue (non-cancelled)."""
    df = clean_df[~clean_df["is_cancelled"]].copy()
    df["Month"] = df["InvoiceDate"].dt.to_period("M").dt.to_timestamp()
    monthly = df.groupby("Month")["Revenue"].sum().reset_index()
    fig = px.area(
        monthly,
        x="Month", y="Revenue",
        labels={"Revenue": "Revenue (£)", "Month": "Month"},
        color_discrete_sequence=[PRIMARY],
    )
    fig.update_traces(fill="tozeroy", fillcolor="rgba(79,142,247,0.15)", line_color=PRIMARY)
    return _apply_layout(fig, "Monthly Revenue Trend")


def monthly_orders_chart(clean_df: pd.DataFrame) -> go.Figure:
    """Bar chart of monthly order count."""
    df = clean_df[~clean_df["is_cancelled"]].copy()
    df["Month"] = df["InvoiceDate"].dt.to_period("M").dt.to_timestamp()
    monthly = df.groupby("Month")["InvoiceNo"].nunique().reset_index()
    monthly.columns = ["Month", "Orders"]
    fig = px.bar(
        monthly, x="Month", y="Orders",
        color_discrete_sequence=[ACCENT],
    )
    return _apply_layout(fig, "Monthly Order Volume")


def top_products_chart(
    clean_df: pd.DataFrame, by: str = "Revenue", top_n: int = 15
) -> go.Figure:
    """Horizontal bar chart of top products."""
    df = clean_df[~clean_df["is_cancelled"]].copy()
    if by == "Revenue":
        top = (
            df.groupby("Description")["Revenue"].sum()
            .nlargest(top_n).reset_index()
        )
    else:
        top = (
            df.groupby("Description")["Quantity"].sum()
            .nlargest(top_n).reset_index()
        )
    fig = px.bar(
        top[::-1],
        x=by, y="Description",
        orientation="h",
        color_discrete_sequence=[SUCCESS],
    )
    fig.update_layout(yaxis=dict(tickfont=dict(size=10)))
    return _apply_layout(fig, f"Top {top_n} Products by {by}")


def revenue_by_country_chart(clean_df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Choropleth or bar chart of revenue by country."""
    df = clean_df[~clean_df["is_cancelled"]].copy()
    by_country = (
        df.groupby("Country")["Revenue"].sum()
        .nlargest(top_n).reset_index()
    )
    fig = px.bar(
        by_country[::-1],
        x="Revenue", y="Country",
        orientation="h",
        color="Revenue",
        color_continuous_scale=[[0, "#1a2744"], [1, PRIMARY]],
    )
    fig.update_coloraxes(showscale=False)
    return _apply_layout(fig, f"Revenue by Country (Top {top_n})")


def order_value_distribution(customer_features: pd.DataFrame) -> go.Figure:
    """Histogram of average order values (log-scaled)."""
    vals = customer_features["avg_order_value"].dropna()
    fig = px.histogram(
        vals,
        nbins=60,
        labels={"value": "Avg Order Value (£)", "count": "Customers"},
        color_discrete_sequence=[WARNING],
        log_x=True,
    )
    return _apply_layout(fig, "Distribution of Average Order Value")


def purchase_frequency_distribution(customer_features: pd.DataFrame) -> go.Figure:
    freqs = customer_features["frequency"].clip(upper=50)
    fig = px.histogram(
        freqs, nbins=50,
        labels={"value": "Number of Orders", "count": "Customers"},
        color_discrete_sequence=[ACCENT],
    )
    return _apply_layout(fig, "Purchase Frequency Distribution")


def repeat_vs_onetime_chart(customer_features: pd.DataFrame) -> go.Figure:
    counts = customer_features["repeat_rate"].value_counts().reset_index()
    counts.columns = ["Type", "Count"]
    counts["Type"] = counts["Type"].map({1: "Repeat Customers", 0: "One-Time Customers"})
    fig = px.pie(
        counts, names="Type", values="Count",
        color_discrete_sequence=[PRIMARY, MUTED],
        hole=0.45,
    )
    fig.update_traces(textfont_color=FONT_COLOR)
    return _apply_layout(fig, "Repeat vs One-Time Customers")


def customer_spending_distribution(customer_features: pd.DataFrame) -> go.Figure:
    vals = customer_features["monetary"].clip(lower=0)
    fig = px.histogram(
        np.log1p(vals), nbins=60,
        labels={"value": "log(1 + Total Spend £)", "count": "Customers"},
        color_discrete_sequence=[SUCCESS],
    )
    return _apply_layout(fig, "Customer Spending Distribution (log scale)")


# ── Segmentation Charts ───────────────────────────────────────────────────────

def cluster_scatter(
    pca_coords: np.ndarray,
    labels: np.ndarray,
    segment_names: dict[int, str],
) -> go.Figure:
    """2-D PCA scatter coloured by cluster."""
    df = pd.DataFrame(pca_coords, columns=["PC1", "PC2"])
    df["Cluster"] = labels
    df["Segment"] = df["Cluster"].map(segment_names)
    fig = px.scatter(
        df, x="PC1", y="PC2", color="Segment",
        opacity=0.7,
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(marker=dict(size=4))
    return _apply_layout(fig, "Customer Segments (PCA 2-D Projection)")


def elbow_chart(inertias: dict[int, float]) -> go.Figure:
    ks = sorted(inertias.keys())
    vals = [inertias[k] for k in ks]
    fig = go.Figure(go.Scatter(
        x=ks, y=vals, mode="lines+markers",
        line=dict(color=PRIMARY, width=2),
        marker=dict(color=ACCENT, size=8),
    ))
    fig.update_layout(
        xaxis_title="Number of Clusters (K)",
        yaxis_title="Inertia (WCSS)",
    )
    return _apply_layout(fig, "Elbow Method — Optimal K")


def silhouette_chart(silhouette_scores: dict[int, float]) -> go.Figure:
    ks = sorted(silhouette_scores.keys())
    vals = [silhouette_scores[k] for k in ks]
    fig = go.Figure(go.Bar(
        x=ks, y=vals,
        marker_color=[SUCCESS if v == max(vals) else MUTED for v in vals],
    ))
    fig.update_layout(xaxis_title="K", yaxis_title="Silhouette Score")
    return _apply_layout(fig, "Silhouette Score by K")


# ── Churn Charts ──────────────────────────────────────────────────────────────

def confusion_matrix_chart(cm: np.ndarray, model_name: str = "") -> go.Figure:
    labels = ["No Churn", "Churn"]
    fig = ff.create_annotated_heatmap(
        z=cm[::-1],
        x=labels, y=labels[::-1],
        colorscale=[[0, BG], [1, PRIMARY]],
        showscale=False,
        font_colors=[FONT_COLOR],
    )
    fig.update_layout(
        xaxis=dict(title="Predicted", tickfont=dict(color=FONT_COLOR)),
        yaxis=dict(title="Actual", tickfont=dict(color=FONT_COLOR)),
    )
    return _apply_layout(fig, f"Confusion Matrix — {model_name}")


def feature_importance_chart(importances: pd.Series, title: str = "Feature Importance") -> go.Figure:
    df = importances.reset_index()
    df.columns = ["Feature", "Importance"]
    fig = px.bar(
        df.sort_values("Importance"),
        x="Importance", y="Feature",
        orientation="h",
        color="Importance",
        color_continuous_scale=[[0, PAPER_BG], [1, ACCENT]],
    )
    fig.update_coloraxes(showscale=False)
    return _apply_layout(fig, title)


def churn_probability_histogram(probas: np.ndarray) -> go.Figure:
    fig = px.histogram(
        probas, nbins=30,
        labels={"value": "Churn Probability", "count": "Customers"},
        color_discrete_sequence=[DANGER],
    )
    return _apply_layout(fig, "Distribution of Churn Probabilities")


def roc_curve_chart(
    y_true: np.ndarray,
    lr_probas: np.ndarray,
    rf_probas: np.ndarray,
    lr_auc: float,
    rf_auc: float,
) -> go.Figure:
    from sklearn.metrics import roc_curve

    def _roc(y, p):
        fpr, tpr, _ = roc_curve(y, p)
        return fpr, tpr

    fig = go.Figure()
    for probas, name, auc, color in [
        (lr_probas, "Logistic Regression", lr_auc, WARNING),
        (rf_probas, "Random Forest", rf_auc, PRIMARY),
    ]:
        if len(probas) > 0 and not np.isnan(auc):
            fpr, tpr = _roc(y_true, probas)
            fig.add_trace(go.Scatter(
                x=fpr, y=tpr, mode="lines",
                name=f"{name} (AUC={auc:.3f})",
                line=dict(color=color, width=2),
            ))

    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1], mode="lines",
        line=dict(color=MUTED, dash="dash"),
        name="Random",
        showlegend=True,
    ))
    fig.update_layout(
        xaxis_title="False Positive Rate",
        yaxis_title="True Positive Rate",
    )
    return _apply_layout(fig, "ROC Curves — Churn Models")


# ── Next-Purchase Charts ──────────────────────────────────────────────────────

def prediction_vs_actual_chart(
    y_true: np.ndarray, y_pred: np.ndarray
) -> go.Figure:
    sample = min(len(y_true), 500)
    idx = np.random.default_rng(42).choice(len(y_true), sample, replace=False)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=y_true[idx], y=y_pred[idx], mode="markers",
        marker=dict(color=PRIMARY, opacity=0.5, size=5),
        name="Predicted vs Actual",
    ))
    max_val = max(y_true.max(), y_pred.max()) if len(y_true) > 0 else 100
    fig.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val], mode="lines",
        line=dict(color=MUTED, dash="dash"), name="Perfect",
    ))
    fig.update_layout(
        xaxis_title="Actual Days",
        yaxis_title="Predicted Days",
    )
    return _apply_layout(fig, "Predicted vs Actual Days to Next Purchase")


# ── Customer profile charts ───────────────────────────────────────────────────

def spending_over_time(orders_df: pd.DataFrame) -> go.Figure:
    if orders_df.empty:
        return go.Figure()
    df = orders_df.sort_values("InvoiceDate")
    fig = px.bar(
        df, x="InvoiceDate", y="Revenue",
        color_discrete_sequence=[PRIMARY],
        labels={"Revenue": "Order Revenue (£)", "InvoiceDate": "Date"},
    )
    return _apply_layout(fig, "Spending Over Time")
