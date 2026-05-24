"""
services/ml_engine/anomaly_detector.py — Component B: AI Early Warning Engine

Pipeline:
  1. Fetch AMRRecord rows from DB by record_id list
  2. Preprocess → numerical feature matrix
  3. IsolationForest fit + predict
  4. For credible anomalies (score < 0, quality > 0.7):
     a. Compute deterministic SHAP stub (real-SHAP ready interface)
     b. Persist Alert to DB
     c. Trigger LLMAdvisoryEngine for both user roles
     d. Dispatch SMS via SMSService
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
from sqlalchemy.orm import Session

from src.models.entities import Alert, AMRRecord

logger = logging.getLogger(__name__)

# ── SHAP Demo Scenario Weights ────────────────────────────────────────────────────
# Hardcoded for July 14 scripted demo scenarios. Replace _compute_shap_stub()
# with a real shap.TreeExplainer call post-MVP without changing the interface.
_HIGH_RISK_PATHOGENS = {"E. coli", "K. pneumoniae", "Salmonella spp.", "Campylobacter spp."}
_HIGH_RISK_COUNTIES = {"Nairobi", "Kiambu", "Mombasa"}
_HIGH_RISK_DRUGS = {"Meropenem", "Colistin", "Ceftriaxone"}


class AMRAnomalyEngine:
    """
    Component B: IsolationForest-based anomaly detection engine with
    SHAP explainability stub and downstream LLM + SMS triggers.
    """

    def __init__(self, db: Session, contamination: float = 0.05):
        self.db = db
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.county_encoder = LabelEncoder()
        self.pathogen_encoder = LabelEncoder()

    # ── Preprocessing ─────────────────────────────────────────────────────────────

    def preprocess(self, records: List[AMRRecord]) -> pd.DataFrame:
        """
        Converts AMRRecord ORM objects into a numerical feature matrix.
        All encoders are fit on the current batch (safe for small batches).
        """
        sir_map = {"Sensitive": 0, "Intermediate": 1, "Resistant": 2}
        sector_map = {"human": 0, "animal": 1, "environment": 2}

        rows = []
        for r in records:
            sir = sir_map.get(r.result_value, 1)
            sector_raw = r.sector.value if hasattr(r.sector, "value") else str(r.sector).split(".")[-1].lower()
            sector_num = sector_map.get(sector_raw, 0)
            rows.append({
                "result_numeric": sir,
                "sector_encoded": sector_num,
                "data_quality_score": r.data_quality_score or 1.0,
                "county_raw": r.county,
                "pathogen_raw": r.pathogen_name,
                "drug_raw": r.antimicrobial_agent,
            })

        df = pd.DataFrame(rows)
        df["county_encoded"] = self.county_encoder.fit_transform(df["county_raw"].fillna("Unknown"))
        df["pathogen_encoded"] = self.pathogen_encoder.fit_transform(df["pathogen_raw"].fillna("Unknown"))

        return df[["result_numeric", "sector_encoded", "data_quality_score", "county_encoded", "pathogen_encoded"]]

    # ── SHAP Stub (Demo-Ready, Real-SHAP Interface) ───────────────────────────────

    def _compute_shap_stub(self, record: AMRRecord, anomaly_score: float) -> Dict[str, Any]:
        """
        Deterministic feature-weight map that matches the July 14 scripted demo scenarios.
        Interface identical to what shap.TreeExplainer would produce — swap this method
        post-MVP without changing any callers.

        Weights sum to 1.0 and represent contribution to the anomaly signal:
          - county_weight: elevated for high-surveillance counties (Nairobi, Kiambu)
          - pathogen_risk_weight: elevated for WHO priority pathogens
          - drug_class_weight: elevated for Reserve/Watch AWaRe antimicrobials
          - sector_weight: elevated for poultry/animal sector (One Health signal)
          - quality_penalty: positive = high quality data (weight on trust)
        """
        county_w = 0.40 if record.county in _HIGH_RISK_COUNTIES else 0.15
        pathogen_w = 0.35 if record.pathogen_name in _HIGH_RISK_PATHOGENS else 0.10
        drug_w = 0.30 if record.antimicrobial_agent in _HIGH_RISK_DRUGS else 0.10
        sector_raw = record.sector.value if hasattr(record.sector, "value") else "human"
        sector_w = 0.20 if sector_raw == "animal" else 0.05
        quality_w = round(record.data_quality_score or 1.0, 3)

        # Normalize to sum to ~1.0
        total = county_w + pathogen_w + drug_w + sector_w
        return {
            "county_weight": round(county_w / total, 4),
            "pathogen_risk_weight": round(pathogen_w / total, 4),
            "drug_class_weight": round(drug_w / total, 4),
            "sector_weight": round(sector_w / total, 4),
            "quality_signal": quality_w,
            "raw_anomaly_score": round(anomaly_score, 6),
            "method": "shap_stub_v1_demo",
        }

    # ── Main Detection Pipeline ───────────────────────────────────────────────────

    def run_detection_pipeline(self, record_ids: List[int]) -> List[Alert]:
        """
        Fetches records from DB, runs IsolationForest, persists credible Alerts,
        and triggers downstream LLM advisory + SMS dispatch.

        Returns the list of Alert objects that were created.
        """
        if not record_ids:
            logger.warning("run_detection_pipeline called with empty record_ids")
            return []

        records = (
            self.db.query(AMRRecord)
            .filter(AMRRecord.id.in_(record_ids))
            .all()
        )

        if len(records) < 2:
            logger.info("Insufficient records (%d) for anomaly detection. Minimum 2 required.", len(records))
            return []

        # ── Feature matrix ──────────────────────────────────────────────────────
        feature_df = self.preprocess(records)
        X = feature_df.values

        # ── Fit + predict ───────────────────────────────────────────────────────
        self.model.fit(X)
        predictions = self.model.predict(X)          # -1 = anomaly, 1 = normal
        scores = self.model.decision_function(X)     # More negative = more anomalous

        created_alerts: List[Alert] = []

        for i, record in enumerate(records):
            is_anomaly = predictions[i] == -1
            quality_ok = (record.data_quality_score or 0.0) > 0.7

            if not (is_anomaly and quality_ok):
                continue

            anomaly_score = float(scores[i])
            # hotspot_magnitude: invert and normalize to [0, 1] for frontend display
            hotspot_magnitude = float(np.clip(abs(anomaly_score) * 10, 0, 1))
            shap_stub = self._compute_shap_stub(record, anomaly_score)

            alert = Alert(
                record_id=record.id,
                anomaly_score=anomaly_score,
                hotspot_magnitude=hotspot_magnitude,
                feature_importance=shap_stub,
            )
            self.db.add(alert)
            self.db.flush()  # Get alert.id before downstream calls

            logger.info(
                "Alert created — Record %d | County: %s | Pathogen: %s | Score: %.4f",
                record.id, record.county, record.pathogen_name, anomaly_score,
            )

            # ── Trigger LLM advisory for both roles ──────────────────────────────
            self._trigger_advisory(alert=alert, record=record)

            created_alerts.append(alert)

        self.db.commit()
        logger.info("Detection pipeline complete. %d alert(s) created.", len(created_alerts))
        return created_alerts

    # ── Downstream Triggers ───────────────────────────────────────────────────────

    def _trigger_advisory(self, alert: Alert, record: AMRRecord) -> None:
        """
        Calls LLMAdvisoryEngine for National Coordinator and County Veterinarian roles,
        then dispatches an SMS via SMSService.
        """
        import asyncio
        from src.services.intelligence.llm_advisory import LLMAdvisoryEngine
        from src.services.notifications.sms_service import SMSService

        advisory_engine = LLMAdvisoryEngine()

        for role in ["National Coordinator", "County Veterinarian"]:
            try:
                advisory_engine.generate_advisory(
                    alert_id=alert.id,
                    role=role,
                    db=self.db,
                )
            except Exception as exc:
                logger.error("LLM advisory failed for role '%s' on alert %d: %s", role, alert.id, exc)

        # SMS dispatch (async) — fire-and-forget pattern
        sms = SMSService()
        message = sms.build_stewardship_message(
            county=record.county,
            pathogen=record.pathogen_name,
            drug=record.antimicrobial_agent,
            role="County Veterinarian",
        )
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(sms.dispatch_alert(phone="+254700000000", message=message))
            loop.close()
        except Exception as exc:
            logger.warning("SMS dispatch failed for alert %d: %s", alert.id, exc)
