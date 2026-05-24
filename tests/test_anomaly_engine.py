"""
tests/test_anomaly_engine.py — Unit tests for AMRAnomalyEngine (Component B)

Validates:
  - Preprocessing: ORM records → correct numerical feature matrix
  - SHAP stub: high-risk inputs produce elevated weights
  - Detection pipeline: credible anomalies generate Alert rows with correct fields
  - Quality gate: low-quality records (score ≤ 0.7) are suppressed even if anomalous
  - Short-batch safety: < 2 records returns empty without crashing
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.services.ml_engine.anomaly_detector import AMRAnomalyEngine, _HIGH_RISK_COUNTIES, _HIGH_RISK_PATHOGENS


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_record(
    db_session,
    county="Nairobi",
    pathogen="E. coli",
    drug="Meropenem",
    sector_str="human",
    result_value="Resistant",
    data_quality_score=0.95,
):
    """Helper to build and flush a minimal AMRRecord."""
    from src.models.entities import AMRRecord, SectorEnum
    from src.models.entities import SectorEnum as SE
    sector_map = {"human": SE.HUMAN, "animal": SE.ANIMAL, "environment": SE.ENVIRONMENT}

    record = AMRRecord(
        sector=sector_map.get(sector_str, SE.HUMAN),
        pathogen_name=pathogen,
        antimicrobial_agent=drug,
        county=county,
        result_value=result_value,
        data_quality_score=data_quality_score,
        is_synthetic=1,
    )
    db_session.add(record)
    db_session.flush()
    return record


# ── Preprocessing ─────────────────────────────────────────────────────────────

class TestPreprocessing:
    def test_returns_correct_feature_columns(self, db_session):
        engine = AMRAnomalyEngine(db=db_session)
        r1 = _make_record(db_session, county="Nairobi", result_value="Resistant")
        r2 = _make_record(db_session, county="Kiambu", result_value="Sensitive")
        df = engine.preprocess([r1, r2])

        assert set(df.columns) == {
            "result_numeric", "sector_encoded", "data_quality_score",
            "county_encoded", "pathogen_encoded"
        }
        assert len(df) == 2

    def test_resistant_maps_to_2(self, db_session):
        engine = AMRAnomalyEngine(db=db_session)
        r = _make_record(db_session, result_value="Resistant")
        df = engine.preprocess([r])
        assert df["result_numeric"].iloc[0] == 2

    def test_sensitive_maps_to_0(self, db_session):
        engine = AMRAnomalyEngine(db=db_session)
        r = _make_record(db_session, result_value="Sensitive")
        df = engine.preprocess([r])
        assert df["result_numeric"].iloc[0] == 0

    def test_animal_sector_maps_to_1(self, db_session):
        engine = AMRAnomalyEngine(db=db_session)
        r = _make_record(db_session, sector_str="animal")
        df = engine.preprocess([r])
        assert df["sector_encoded"].iloc[0] == 1


# ── SHAP Stub ─────────────────────────────────────────────────────────────────

class TestSHAPStub:
    def test_high_risk_county_yields_elevated_county_weight(self, db_session):
        engine = AMRAnomalyEngine(db=db_session)
        record = _make_record(db_session, county="Nairobi")
        stub = engine._compute_shap_stub(record, anomaly_score=-0.3)

        assert "county_weight" in stub
        assert stub["county_weight"] >= 0.30  # Should be highest single weight

    def test_low_risk_county_yields_lower_weight(self, db_session):
        engine = AMRAnomalyEngine(db=db_session)
        record_high = _make_record(db_session, county="Nairobi")
        record_low = _make_record(db_session, county="Marsabit")

        stub_high = engine._compute_shap_stub(record_high, anomaly_score=-0.3)
        stub_low = engine._compute_shap_stub(record_low, anomaly_score=-0.3)

        assert stub_high["county_weight"] > stub_low["county_weight"]

    def test_stub_contains_required_keys(self, db_session):
        engine = AMRAnomalyEngine(db=db_session)
        record = _make_record(db_session)
        stub = engine._compute_shap_stub(record, anomaly_score=-0.2)

        required = {"county_weight", "pathogen_risk_weight", "drug_class_weight",
                    "sector_weight", "quality_signal", "raw_anomaly_score", "method"}
        assert required.issubset(set(stub.keys()))

    def test_stub_method_is_demo_marker(self, db_session):
        engine = AMRAnomalyEngine(db=db_session)
        record = _make_record(db_session)
        stub = engine._compute_shap_stub(record, anomaly_score=-0.1)
        assert stub["method"] == "shap_stub_v1_demo"


# ── Detection Pipeline ─────────────────────────────────────────────────────────

class TestDetectionPipeline:
    def test_short_batch_returns_empty(self, db_session):
        """< 2 records should return [] without crashing."""
        r = _make_record(db_session)
        engine = AMRAnomalyEngine(db=db_session)
        alerts = engine.run_detection_pipeline(record_ids=[r.id])
        assert alerts == []

    def test_empty_id_list_returns_empty(self, db_session):
        engine = AMRAnomalyEngine(db=db_session)
        alerts = engine.run_detection_pipeline(record_ids=[])
        assert alerts == []

    def test_low_quality_records_suppressed(self, db_session):
        """Records with data_quality_score ≤ 0.7 must not generate alerts even if anomalous."""
        records = [
            _make_record(db_session, county=f"County_{i}", data_quality_score=0.5)
            for i in range(5)
        ]
        engine = AMRAnomalyEngine(db=db_session)

        # Patch IsolationForest to flag everything as anomalous
        import numpy as np
        engine.model.predict = MagicMock(return_value=np.array([-1] * len(records)))
        engine.model.decision_function = MagicMock(return_value=np.array([-0.5] * len(records)))
        engine.model.fit = MagicMock()

        with patch.object(engine, "_trigger_advisory"):
            alerts = engine.run_detection_pipeline(
                record_ids=[r.id for r in records]
            )

        assert alerts == []

    def test_high_quality_anomalous_record_creates_alert(self, db_session):
        """A credible anomaly (score<0, quality>0.7) must produce a persisted Alert."""
        import numpy as np

        records = [
            _make_record(db_session, county="Nairobi", data_quality_score=0.95),
            _make_record(db_session, county="Kiambu", data_quality_score=0.90),
        ]
        engine = AMRAnomalyEngine(db=db_session)
        engine.model.predict = MagicMock(return_value=np.array([-1, -1]))
        engine.model.decision_function = MagicMock(return_value=np.array([-0.4, -0.3]))
        engine.model.fit = MagicMock()

        with patch.object(engine, "_trigger_advisory"):
            alerts = engine.run_detection_pipeline(
                record_ids=[r.id for r in records]
            )

        assert len(alerts) == 2
        for alert in alerts:
            assert alert.id is not None
            assert alert.anomaly_score < 0
            assert alert.hotspot_magnitude >= 0
            assert isinstance(alert.feature_importance, dict)
            assert "county_weight" in alert.feature_importance

    def test_alert_fields_match_schema(self, db_session):
        """Alert.anomaly_score, hotspot_magnitude, feature_importance must be set correctly."""
        import numpy as np

        r1 = _make_record(db_session, county="Nairobi", data_quality_score=0.95)
        r2 = _make_record(db_session, county="Kiambu", data_quality_score=0.90)
        engine = AMRAnomalyEngine(db=db_session)
        engine.model.predict = MagicMock(return_value=np.array([-1, 1]))
        engine.model.decision_function = MagicMock(return_value=np.array([-0.3, 0.1]))
        engine.model.fit = MagicMock()

        with patch.object(engine, "_trigger_advisory"):
            alerts = engine.run_detection_pipeline(record_ids=[r1.id, r2.id])

        assert len(alerts) == 1
        a = alerts[0]
        assert a.anomaly_score == pytest.approx(-0.3, abs=1e-5)
        assert 0 <= a.hotspot_magnitude <= 1
        assert a.feature_importance.get("method") == "shap_stub_v1_demo"
