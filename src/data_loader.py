"""
src/data_loader.py
──────────────────
Handles loading the UCI Online Retail dataset from an Excel or CSV file.
Returns a raw DataFrame; no transformations are applied here so that the
caller can inspect the raw data before cleaning.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
}


def validate_columns(df: pd.DataFrame) -> list[str]:
    """Return a list of required columns that are missing from *df*."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    return missing


def load_data(
    filepath: str | Path,
    sheet_name: str = "Online Retail",
    nrows: Optional[int] = None,
) -> pd.DataFrame:
    """
    Load the UCI Online Retail dataset from an Excel (.xlsx) or CSV file.

    Parameters
    ----------
    filepath : str | Path
        Path to the dataset file.
    sheet_name : str
        Sheet name to read when the file is Excel. Ignored for CSV files.
    nrows : int | None
        If given, only the first *nrows* rows are loaded (useful for testing).

    Returns
    -------
    pd.DataFrame
        Raw DataFrame with the original column names preserved.

    Raises
    ------
    FileNotFoundError
        If *filepath* does not exist.
    ValueError
        If required columns are missing after loading.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(
            f"Dataset not found at '{filepath}'. "
            "Please download 'Online Retail.xlsx' from "
            "https://archive.ics.uci.edu/dataset/352/online+retail "
            "and place it in the data/ directory, or upload it via the Settings page."
        )

    suffix = filepath.suffix.lower()
    logger.info("Loading dataset from %s (format=%s)", filepath, suffix)

    if suffix in {".xlsx", ".xls"}:
        # Try the expected sheet name first; fall back to first sheet
        try:
            df = pd.read_excel(
                filepath,
                sheet_name=sheet_name,
                engine="openpyxl",
                nrows=nrows,
            )
        except Exception:
            logger.warning(
                "Sheet '%s' not found; reading first sheet instead.", sheet_name
            )
            df = pd.read_excel(
                filepath,
                sheet_name=0,
                engine="openpyxl",
                nrows=nrows,
            )
    elif suffix == ".csv":
        df = pd.read_csv(filepath, nrows=nrows, low_memory=False)
    else:
        raise ValueError(
            f"Unsupported file format '{suffix}'. Only .xlsx, .xls, and .csv are supported."
        )

    # Normalise column names (strip whitespace)
    df.columns = [c.strip() for c in df.columns]

    missing = validate_columns(df)
    if missing:
        raise ValueError(
            f"The file is missing required columns: {missing}. "
            "Please check that you are using a compatible version of the UCI Online Retail dataset."
        )

    logger.info("Loaded %d rows and %d columns.", len(df), df.shape[1])
    return df


def load_from_upload(uploaded_file, sheet_name: str = "Online Retail") -> pd.DataFrame:
    """
    Load data from a Streamlit UploadedFile object.

    Parameters
    ----------
    uploaded_file : streamlit.runtime.uploaded_file_manager.UploadedFile
        The file object returned by ``st.file_uploader``.
    sheet_name : str
        Sheet name for Excel files.

    Returns
    -------
    pd.DataFrame
        Raw DataFrame.
    """
    name = uploaded_file.name.lower()
    if name.endswith((".xlsx", ".xls")):
        try:
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name, engine="openpyxl")
        except Exception:
            df = pd.read_excel(uploaded_file, sheet_name=0, engine="openpyxl")
    elif name.endswith(".csv"):
        df = pd.read_csv(uploaded_file, low_memory=False)
    else:
        raise ValueError("Only .xlsx, .xls, and .csv files are supported.")

    df.columns = [c.strip() for c in df.columns]
    missing = validate_columns(df)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df
