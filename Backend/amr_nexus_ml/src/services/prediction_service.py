import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.ml import (
    get_model,
    get_anomaly_model,
    get_preprocessor,
    get_feature_names,
    get_numeric_indices,
    get_shap_explainer,
)
from src.core.sms import send_sms_alert
from src.db.models import AMRIsolateRecord
from src.services.alert_service import trigger_alert
from src.utils.logger import logger
from src.utils.helpers import generate_shap_summary


class PredictionService:
    def __init__(self, db_session: Session) -> None:
        self.db = db_session

    async def predict(
        self, record: Any, background_tasks: Optional[BackgroundTasks] = None
    ) -> Dict[str, Any]:
        try:
            if hasattr(record, "model_dump"):
                input_dict = record.model_dump()
            elif hasattr(record, "dict"):
                input_dict = record.dict()
            else:
                input_dict = dict(record)

            features = settings.FRONTEND_FEATURES

            for col in features:
                if col not in input_dict:
                    if col == 'prior_antibiotic_exposure':
                        input_dict[col] = False
                    elif col == 'sample_month':
                        input_dict[col] = 1
                    else:
                        input_dict[col] = ''

            df = pd.DataFrame([input_dict])[features]

            if 'prior_antibiotic_exposure' in df.columns:
                df['prior_antibiotic_exposure'] = df['prior_antibiotic_exposure'].astype(bool)

            logger.info(f"Input DataFrame columns: {df.columns.tolist()}")
            logger.info(f"Input DataFrame dtypes: {df.dtypes.to_dict()}")

            preprocessor = get_preprocessor()
            if preprocessor is None:
                raise RuntimeError("Preprocessor not loaded. Please train models first.")

            X = preprocessor.transform(df)
            X_arr = X.toarray() if hasattr(X, "toarray") else (X.values if hasattr(X, "values") else np.array(X))
            if X_arr.ndim == 1:
                X_arr = X_arr.reshape(1, -1)

            mdr_prob = float(get_model().predict_proba(X_arr)[0, 1])
            mdr_flag = bool(mdr_prob >= 0.5)

            numeric_indices = get_numeric_indices()
            if numeric_indices is None or len(numeric_indices) == 0:
                X_numeric = X_arr
            else:
                X_numeric = X_arr[:, numeric_indices]

            anomaly_score = float(-get_anomaly_model().score_samples(X_numeric)[0])
            anomaly_detected = bool(get_anomaly_model().predict(X_numeric)[0] == -1)

            shap_top_feature = None
            shap_val = None
            shap_summary = None
            explainer = get_shap_explainer()
            if explainer is not None:
                shap_values = explainer.shap_values(X_arr)
                shap_abs = np.abs(shap_values[0])
                top_idx = int(np.argmax(shap_abs))
                feature_list = get_feature_names()
                shap_top_feature = str(
                    feature_list[top_idx]
                    if isinstance(feature_list, (list, tuple))
                    else feature_list.tolist()[top_idx]
                )
                shap_val = float(shap_values[0][top_idx])
                shap_summary = generate_shap_summary(
                    shap_values,
                    feature_list,
                    mdr_prob,
                    settings.SHAP_TOP_FEATURES,
                )

            db_record = AMRIsolateRecord(
                record_id=uuid.uuid4(),
                created_at=datetime.now(timezone.utc),
                submission_type="REAL",
                pathogen_code=input_dict.get("pathogen_code"),
                sector=input_dict.get("sector"),
                sub_sector=input_dict.get("sub_sector"),
                specimen_type=input_dict.get("specimen_type"),
                county=input_dict.get("county"),
                sample_month=int(input_dict.get("sample_month", 1)),
                antibiotic_class=input_dict.get("antibiotic_class"),
                test_method=input_dict.get("test_method"),
                patient_age_years=float(input_dict["patient_age_years"]) if input_dict.get("patient_age_years") else None,
                patient_sex=input_dict.get("patient_sex"),
                ward_type=input_dict.get("ward_type"),
                prior_antibiotic_exposure=bool(input_dict.get("prior_antibiotic_exposure", False)),
                infection_origin=input_dict.get("infection_origin"),
                animal_species=input_dict.get("animal_species"),
                production_system=input_dict.get("production_system"),
                urban_rural=input_dict.get("urban_rural"),
                mdr_flag=mdr_flag,
                mdr_probability=mdr_prob,
                anomaly_flag=anomaly_detected,
                anomaly_score=anomaly_score,
                shap_top_feature=shap_top_feature,
                shap_value=shap_val,
                shap_summary=shap_summary,
                model_version="1.0.0",
            )

            self.db.add(db_record)
            self.db.commit()
            self.db.refresh(db_record)

            if anomaly_detected or mdr_flag or mdr_prob >= 0.70:
                trigger_alert(db_record, background_tasks)
                phone = input_dict.get("phone_number")
                if phone and settings.ENABLE_SMS:
                    msg = (
                        f"AMR Alert: {input_dict.get('pathogen_code', 'unknown').upper()} "
                        f"anomaly in {input_dict.get('county', 'unknown')}. "
                        f"MDR prob: {mdr_prob*100:.1f}%"
                    )
                    background_tasks.add_task(send_sms_alert, phone, msg)

            return {
                "mdr_flag": int(mdr_flag),
                "mdr_probability": mdr_prob,
                "anomaly_detected": int(anomaly_detected),
                "anomaly_score": anomaly_score,
                "shap_top_feature": shap_top_feature,
                "shap_value": shap_val,
                "shap_summary": shap_summary,
            }
        except Exception as e:
            logger.exception(f"Prediction failed: {str(e)}")
            raise RuntimeError(f"Prediction failed: {str(e)}") from e