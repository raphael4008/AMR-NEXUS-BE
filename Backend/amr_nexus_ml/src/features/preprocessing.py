import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from joblib import dump, load
from src.utils.logger import logger


class FeaturePreprocessor:
    def __init__(self) -> None:
        self.scaler: StandardScaler = StandardScaler()
        self.ohe: Optional[OneHotEncoder] = None
        self.cat_cols: List[str] = [
            "sector",
            "specimen_type",
            "antibiotic_class",
            "test_method",
            "age_group",
            "gender",
            "facility",
            "pathogen_code",
            "county",
            "sub_sector",
        ]
        self.numeric_cols: List[str] = [
            "patient_age_years",
            "sample_month",
            "prior_antibiotic_use",
            "hospitalised",
        ]
        self._feature_names_out: List[str] = []

    def fit(self, df: pd.DataFrame) -> "FeaturePreprocessor":
        df_clean = self._ensure_columns(df.copy())
        df_clean = self._clean_binary_strings(df_clean)
        df_clean = self._handle_missing(df_clean)

        if self.cat_cols:
            self.ohe = OneHotEncoder(
                sparse_output=False, 
                handle_unknown="ignore", 
                dtype=np.float32
            )
            self.ohe.fit(df_clean[self.cat_cols].astype(str))
            cat_features = list(self.ohe.get_feature_names_out(self.cat_cols))
        else:
            cat_features = []

        if self.numeric_cols:
            self.scaler.fit(df_clean[self.numeric_cols].astype(np.float32))

        self._feature_names_out = self.numeric_cols + cat_features
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df_clean = self._ensure_columns(df.copy())
        df_clean = self._clean_binary_strings(df_clean)
        df_clean = self._handle_missing(df_clean)

        if self.numeric_cols:
            numeric_scaled = self.scaler.transform(
                df_clean[self.numeric_cols].astype(np.float32)
            )
            numeric_df = pd.DataFrame(
                numeric_scaled, 
                columns=self.numeric_cols, 
                index=df_clean.index
            )
        else:
            numeric_df = pd.DataFrame(index=df_clean.index)

        if self.cat_cols and self.ohe is not None:
            ohe_arr = self.ohe.transform(df_clean[self.cat_cols].astype(str))
            ohe_df = pd.DataFrame(
                ohe_arr,
                columns=self.ohe.get_feature_names_out(self.cat_cols),
                index=df_clean.index,
            )
        else:
            ohe_df = pd.DataFrame(index=df_clean.index)

        encoded_df = pd.concat([numeric_df, ohe_df], axis=1)

        for col in self._feature_names_out:
            if col not in encoded_df.columns:
                encoded_df[col] = 0.0

        return encoded_df[self._feature_names_out]

    def _clean_binary_strings(self, df: pd.DataFrame) -> pd.DataFrame:
        binary_fields = ["prior_antibiotic_use", "hospitalised"]
        mapping = {
            "YES": 1,
            "TRUE": 1,
            "1": 1,
            "NO": 0,
            "FALSE": 0,
            "0": 0,
            "-1": 0,
        }

        for field in binary_fields:
            if field in df.columns:
                df[field] = df[field].astype(str).str.strip().str.upper()
                df[field] = df[field].map(mapping).fillna(0).astype(int)

        for field in ["patient_age_years", "sample_month"]:
            if field in df.columns:
                df[field] = pd.to_numeric(df[field], errors="coerce")

        return df

    def _ensure_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        defaults = {
            "specimen_type": "unknown",
            "test_method": "unknown",
            "sub_sector": "unknown",
            "patient_age_years": -1.0,
            "sample_month": 6,
            "pathogen_code": "unknown",
            "county": "unknown",
            "age_group": "Unknown",
            "gender": "U",
            "facility": "Unknown",
            "prior_antibiotic_use": 0,
            "hospitalised": 0,
            "sector": "unknown",
        }
        for col, default in defaults.items():
            if col not in df.columns:
                df[col] = default
        return df

    def _handle_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        df["patient_age_years"] = df["patient_age_years"].fillna(-1.0)
        df["sample_month"] = df["sample_month"].fillna(6)
        df["prior_antibiotic_use"] = df["prior_antibiotic_use"].fillna(0)
        df["hospitalised"] = df["hospitalised"].fillna(0)

        for col in self.cat_cols:
            if col in df.columns:
                df[col] = df[col].fillna("unknown")
        return df

    @property
    def columns(self) -> List[str]:
        return self._feature_names_out

    def save(self, path: str) -> None:
        dump(self, path)

    @classmethod
    def load(cls, path: str) -> "FeaturePreprocessor":
        return load(path)
