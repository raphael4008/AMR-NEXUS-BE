import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Union, Optional

import joblib
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, ValidationError, ConfigDict

from src.features.preprocessing import FeaturePreprocessor
from src.utils.config import config
from src.utils.logger import logger

TARGET_PROBABILITY_THRESHOLD = 0.5


class InferenceRecordSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sector: str = Field(default="unknown")
    sub_sector: str = Field(default="General")
    pathogen_code: str = Field(default="unknown")
    specimen_type: str = Field(default="unknown")
    county: str = Field(default="unknown")
    antibiotic_class: str = Field(default="unknown")
    test_method: str = Field(default="unknown")
    sample_month: int = Field(default=1, ge=1, le=12)
    animal_species: Optional[str] = None
    production_system: Optional[str] = None
    urban_rural: Optional[str] = None
    patient_age_years: Optional[float] = Field(default=None, ge=0)
    patient_sex: Optional[str] = None
    ward_type: Optional[str] = None
    prior_antibiotic_exposure: Optional[str] = None
    infection_origin: Optional[str] = None


class AMRPredictor:
    def __init__(self, model_dir: Optional[Path] = None) -> None:
        self.model_dir = Path(model_dir) if model_dir else config.MODEL_DIR
        if not self.model_dir.exists():
            raise FileNotFoundError(f"Model directory not found: {self.model_dir}")

        logger.info(f"Loading production artifacts from {self.model_dir}")
        try:
            self.model = joblib.load(self.model_dir / "mdr_xgb.pkl")
            self.anomaly_model = joblib.load(self.model_dir / "anomaly_iso.pkl")
            self.preprocessor = FeaturePreprocessor.load(self.model_dir / "preprocessor.pkl")
            self.feature_names = joblib.load(self.model_dir / "feature_names.pkl")
            self.numeric_indices = joblib.load(self.model_dir / "numeric_indices.pkl")
            
            shap_path = self.model_dir / "shap_explainer.pkl"
            self.shap_explainer = joblib.load(shap_path) if shap_path.exists() else None
        except Exception as e:
            logger.error(f"Failed to load vital binary model artifacts: {str(e)}")
            raise

        self._feature_list = (
            self.feature_names if isinstance(self.feature_names, list) else self.feature_names.tolist()
        )
        logger.info("All inference artifacts loaded successfully.")

    def _validate_and_sanitize(self, data: Union[Dict, List[Dict], pd.DataFrame]) -> pd.DataFrame:
        if isinstance(data, pd.DataFrame):
            records = data.to_dict(orient="records")
        elif isinstance(data, dict):
            records = [data]
        elif isinstance(data, list):
            records = data
        else:
            raise TypeError("Unsupported payload type. Must be DataFrame, dict, or list of dicts.")

        validated_records = []
        for index, record in enumerate(records):
            try:
                validated_model = InferenceRecordSchema(**record)
                validated_records.append(validated_model.model_dump())
            except ValidationError as e:
                logger.error(f"Data contract violation dropped at row index {index}: {e.json()}")
                raise

        return pd.DataFrame(validated_records)

    def predict(self, input_data: Union[Dict, List[Dict], pd.DataFrame]) -> pd.DataFrame:
        df_sanitized = self._validate_and_sanitize(input_data)
        
        X = self.preprocessor.transform(df_sanitized)
        X_arr = X.toarray() if hasattr(X, "toarray") else (X.values if hasattr(X, "values") else np.array(X))
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(1, -1)

        mdr_proba = self.model.predict_proba(X_arr)[:, 1]
        mdr_flag = mdr_proba >= TARGET_PROBABILITY_THRESHOLD

        X_numeric = X_arr[:, self.numeric_indices]
        anomaly_scores = -self.anomaly_model.score_samples(X_numeric)
        anomaly_detected = self.anomaly_model.predict(X_numeric) == -1

        shap_top = [None] * X_arr.shape[0]
        shap_vals = [None] * X_arr.shape[0]
        
        if self.shap_explainer is not None:
            shap_values_arr = self.shap_explainer.shap_values(X_arr)
            for i in range(X_arr.shape[0]):
                abs_shap = np.abs(shap_values_arr[i])
                top_idx = np.argmax(abs_shap)
                shap_top[i] = self._feature_list[top_idx]
                shap_vals[i] = float(shap_values_arr[i][top_idx])

        return pd.DataFrame({
            "mdr_flag": mdr_flag.astype(int),
            "mdr_probability": mdr_proba,
            "anomaly_detected": anomaly_detected.astype(int),
            "anomaly_score": anomaly_scores,
            "shap_top_feature": shap_top,
            "shap_value": shap_vals
        })

    def predict_single(self, record: Dict) -> Dict:
        return self.predict([record]).iloc[0].to_dict()


def main() -> None:
    parser = argparse.ArgumentParser(description="AMR runtime inference script")
    parser.add_argument("--input", "-i", required=True, help="Path to input JSON file")
    parser.add_argument("--model-dir", "-m", help="Custom model artifact base directory path")
    parser.add_argument("--output", "-o", help="Path to write output results file path")
    args = parser.parse_args()

    try:
        with open(args.input, "r") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read payload input JSON from disk: {str(e)}")
        sys.exit(1)

    try:
        predictor = AMRPredictor(model_dir=args.model_dir)
        results_df = predictor.predict(data)
        output = results_df.to_dict(orient="records")
    except Exception as e:
        logger.exception(f"Inference execution engine core failure: {str(e)}")
        sys.exit(1)

    if args.output:
        try:
            with open(args.output, "w") as f:
                json.dump(output, f, indent=2)
            logger.info(f"Predictions written to disk path: {args.output}")
        except Exception as e:
            logger.error(f"Failed to save results output mapping payload: {str(e)}")
            sys.exit(1)
    else:
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
