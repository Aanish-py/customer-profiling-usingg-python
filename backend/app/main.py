"""
backend/app/main.py
FastAPI application entry point.
"""

from contextlib import asynccontextmanager
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import (
    API_V1_STR,
    PROJECT_NAME,
    BACKEND_CORS_ORIGINS,
    DEFAULT_DATA_FILE,
)
from backend.app.core.state import state
from backend.app.api.api_router import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("backend.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Auto-load dataset if present
    if os.path.exists(DEFAULT_DATA_FILE):
        try:
            logger.info("Found local dataset at %s. Initializing in background...", DEFAULT_DATA_FILE)
            state.load_dataset_from_file(DEFAULT_DATA_FILE)
            logger.info("Auto-initialization successful!")
        except Exception as e:
            logger.warning("Could not auto-initialize dataset: %s", e)
    else:
        logger.info("No local dataset found at startup. Waiting for user upload/download.")
    yield
    # Shutdown
    logger.info("FastAPI backend shutting down.")


app = FastAPI(
    title=PROJECT_NAME,
    openapi_url=f"{API_V1_STR}/openapi.json",
    docs_url=f"{API_V1_STR}/docs",
    redoc_url=f"{API_V1_STR}/redoc",
    lifespan=lifespan,
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=API_V1_STR)


@app.get("/")
def root():
    return {
        "message": f"Welcome to {PROJECT_NAME}",
        "docs": f"{API_V1_STR}/docs",
        "dataset_ready": state.is_data_loaded,
    }
