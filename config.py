"""
Global configuration constants for the Customer Behavior Intelligence System.
Centralising all tunable parameters here makes it easy to change them
without touching any business-logic module.
"""

import os

# ── Reproducibility ──────────────────────────────────────────────────────────
RANDOM_SEED: int = 42

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
DATA_DIR: str = os.path.join(BASE_DIR, "data")
MODELS_DIR: str = os.path.join(BASE_DIR, "models")
DEFAULT_DATA_FILE: str = os.path.join(DATA_DIR, "Online Retail.xlsx")

# ── Preprocessing defaults ────────────────────────────────────────────────────
MIN_UNIT_PRICE: float = 0.01          # Prices below this are treated as invalid
MIN_QUANTITY: int = 1                  # Minimum quantity for a valid purchase line
MAX_UNIT_PRICE: float = 50_000.0      # Sanity cap; adjust if needed

# ── RFM / Feature-engineering defaults ───────────────────────────────────────
RECENCY_REFERENCE: str = "max_date"   # "max_date" or "today"
MIN_INVOICES_FOR_PREDICTION: int = 3  # Customers need at least this many invoices
                                       # to generate training examples

# ── Segmentation defaults ─────────────────────────────────────────────────────
KMEANS_CLUSTER_RANGE: tuple = (2, 9)  # Range tested by the elbow / silhouette search
DEFAULT_N_CLUSTERS: int = 4

# ── Churn defaults ────────────────────────────────────────────────────────────
DEFAULT_CHURN_WINDOW_DAYS: int = 90
CHURN_CUTOFF_BUFFER_DAYS: int = 90    # Min days before dataset end for cutoff date

# ── Next-purchase defaults ────────────────────────────────────────────────────
TRAIN_FRACTION: float = 0.70
VALIDATION_FRACTION: float = 0.15    # remaining goes to test

# ── Recommendation defaults ───────────────────────────────────────────────────
TOP_N_RECOMMENDATIONS: int = 10
MIN_SUPPORT: float = 0.01            # For association-rule mining (mlxtend)
MIN_CONFIDENCE: float = 0.20

# ── Streamlit / UI ────────────────────────────────────────────────────────────
APP_TITLE: str = "Customer Behavior Intelligence"
APP_ICON: str = "🧠"
PRIMARY_COLOR: str = "#4F8EF7"
BACKGROUND_COLOR: str = "#0D1117"
SECONDARY_BG: str = "#161B22"
ACCENT_COLOR: str = "#58A6FF"
SUCCESS_COLOR: str = "#3FB950"
WARNING_COLOR: str = "#D29922"
DANGER_COLOR: str = "#F85149"
TEXT_COLOR: str = "#E6EDF3"
MUTED_COLOR: str = "#8B949E"
