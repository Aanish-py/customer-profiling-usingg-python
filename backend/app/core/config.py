"""
backend/app/core/config.py
Configuration settings for FastAPI backend.
"""

import os
import sys

# Ensure workspace root is in sys.path so 'src' and root 'config' are importable
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import (
    APP_TITLE,
    DATA_DIR,
    DEFAULT_DATA_FILE,
    MODELS_DIR,
    RANDOM_SEED,
    DEFAULT_CHURN_WINDOW_DAYS,
    DEFAULT_N_CLUSTERS,
    MIN_UNIT_PRICE,
    MIN_QUANTITY,
)

API_V1_STR: str = "/api"
PROJECT_NAME: str = f"{APP_TITLE} API"
BACKEND_CORS_ORIGINS: list[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
