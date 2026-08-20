import sys
from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd
from src.utils.config import config
from src.utils.logger import logger


def load_training_data(limit: Optional[int] = None) -> pd.DataFrame:
    data_path = Path(config.DATA_FILE_PATH)
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    logger.info(f"Loading data securely from {data_path}")

    lower_path = data_path.name.lower()
    try:
        if lower_path.endswith((".xlsx", ".xls")):
            df = pd.read_excel(data_path, engine="openpyxl")
        else:
            try:
                df = pd.read_csv(data_path, encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(data_path, encoding="utf-8-sig")
                except UnicodeDecodeError:
                    df = pd.read_excel(data_path, engine="openpyxl")
    except Exception as e:
        logger.critical(f"Data reader driver failure: {str(e)}")
        raise

    df.columns = df.columns.str.strip()

    if "classification" in df.columns and "resistance_rate" in df.columns:
        logger.info("Dynamic AMR dataset structure detected. Formatting columns...")

        df["mdr_flag"] = (
            df["classification"]
            .astype(str)
            .str.upper()
            .str.strip()
            .isin(config.MDR_CLASSES)
            .astype(int)
        )
        df["sir_result"] = df["resistance_rate"].apply(
            lambda x: "R" if x > config.RESISTANCE_THRESHOLD else "S"
        )

        df["pathogen_code"] = (
            df["pathogen"]
            .astype(str)
            .str.lower()
            .str.strip()
            .map(config.PATHOGEN_MAP)
        )
        df["antibiotic_class"] = (
            df["antibiotic"]
            .astype(str)
            .str.lower()
            .str.strip()
            .map(config.ANTIBIOTIC_MAP)
        )

        df["sector"] = (
            df["sector"]
            .astype(str)
            .str.upper()
            .str.strip()
            .replace(config.SECTOR_REPLACEMENTS)
        )

        if "month" in df.columns:
            df["sample_month"] = pd.to_numeric(df["month"], errors="coerce")
        elif "sample_month" in df.columns:
            df["sample_month"] = pd.to_numeric(
                df["sample_month"], errors="coerce"
            )
        else:
            df["sample_month"] = config.DEFAULT_SAMPLE_MONTH
    else:
        logger.info("Pre-mapped AMR dataset layout detected.")
        for col in config.CRITICAL_COLUMNS:
            if col not in df.columns:
                if col == "mdr_flag":
                    df["mdr_flag"] = 0
                elif col == "sample_month":
                    df["sample_month"] = config.DEFAULT_SAMPLE_MONTH
                else:
                    df[col] = config.DEFAULT_STRING_FALLBACK

        df["sample_month"] = pd.to_numeric(df["sample_month"], errors="coerce")
        df["sector"] = df["sector"].astype(str).str.upper().str.strip()

    if "specimen_type" not in df.columns:
        df["specimen_type"] = config.DEFAULT_STRING_FALLBACK
    if "test_method" not in df.columns:
        df["test_method"] = config.DEFAULT_TEST_METHOD
    if "sub_sector" not in df.columns:
        df["sub_sector"] = df["sector"].apply(
            lambda x: config.SUB_SECTOR_MAP.get(x, config.DEFAULT_STRING_FALLBACK)
        )
    if "patient_age_years" not in df.columns:
        df["patient_age_years"] = config.DEFAULT_AGE_FALLBACK

    if config.GEOGRAPHY_COLUMN in df.columns:
        df[config.GEOGRAPHY_COLUMN] = df[config.GEOGRAPHY_COLUMN].fillna(config.DEFAULT_STRING_FALLBACK)
    else:
        df[config.GEOGRAPHY_COLUMN] = config.DEFAULT_STRING_FALLBACK

    df["sample_month"] = df["sample_month"].fillna(config.DEFAULT_SAMPLE_MONTH).astype(int)

    df = df.dropna(subset=config.CRITICAL_COLUMNS)

    if limit:
        df = df.head(limit)

    logger.info(
        f"Loaded {len(df)} records safely after configuration-driven format mapping."
    )
    return df
