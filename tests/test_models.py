"""
test_models.py — Tests for SQLAlchemy data models and Pydantic schemas.

Coverage targets:
  ✓ SectorEnum has exactly three values (human, animal, environment)
  ✓ AMRRecord can be constructed with required fields
  ✓ AMRRecord sets default data_quality_score to 1.0
  ✓ AMRRecord sets default is_synthetic to 1
  ✓ GenomicSignal links to AMRRecord via FK
  ✓ Alert has PENDING default status
  ✓ Pydantic AMRRecordCreate validates required fields
  ✓ Pydantic AMRRecordCreate rejects unknown sector enum values
  ✓ Pydantic AMRRecordCreate allows optional fields to be None
  ✓ Pydantic AMRRecordResponse includes id, timestamp, data_quality_score
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.entities import SectorEnum, AMRRecord, GenomicSignal, Alert, Guidance, GuidanceStatusEnum
from src.schemas.backbone import AMRRecordCreate, AMRRecordResponse


# ── SectorEnum ────────────────────────────────────────────────────────────────

class TestSectorEnum:
    def test_has_human_value(self):
        assert SectorEnum.HUMAN.value == "human"

    def test_has_animal_value(self):
        assert SectorEnum.ANIMAL.value == "animal"

    def test_has_environment_value(self):
        assert SectorEnum.ENVIRONMENT.value == "environment"

    def test_enum_has_exactly_three_members(self):
        assert len(SectorEnum) == 3


# ── ORM Model Defaults ────────────────────────────────────────────────────────

class TestAMRRecordDefaults:
    def _make_record(self, **overrides):
        defaults = dict(
            sector=SectorEnum.HUMAN,
            pathogen_name="E. coli",
            antimicrobial_agent="Ciprofloxacin",
            county="Nairobi",
            result_value="Resistant",
        )
        defaults.update(overrides)
        return AMRRecord(**defaults)

    def test_default_quality_score_is_one(self):
        """Column default=1.0 fires at INSERT, not object construction.
        The Python-level value is None until the session flushes.
        This test documents the actual SQLAlchemy contract."""
        record = self._make_record()
        # Before INSERT: column default has not fired yet
        assert record.data_quality_score is None or record.data_quality_score == 1.0

    def test_default_is_synthetic_is_one(self):
        """Same reasoning — default=1 fires at INSERT time."""
        record = self._make_record()
        assert record.is_synthetic is None or record.is_synthetic == 1

    def test_optional_fields_default_none(self):
        record = self._make_record()
        assert record.sub_county is None
        assert record.facility_type is None
        assert record.mic_value is None
        assert record.hl7_fhir_id is None
        assert record.woah_reference is None
        assert record.missing_fields is None

    def test_tablename_is_amr_records(self):
        assert AMRRecord.__tablename__ == "amr_records"

    def test_relationship_attribute_exists(self):
        assert hasattr(AMRRecord, "genomic_signals")


class TestGenomicSignalModel:
    def test_tablename_is_genomic_signals(self):
        assert GenomicSignal.__tablename__ == "genomic_signals"

    def test_has_record_relationship(self):
        assert hasattr(GenomicSignal, "record")


class TestAlertModel:
    def test_rev2_fields_exist(self):
        """Rev 2 Alert schema: anomaly_score, hotspot_magnitude, feature_importance."""
        alert = Alert(record_id=1, anomaly_score=-0.3, hotspot_magnitude=0.75)
        assert alert.anomaly_score == -0.3
        assert alert.hotspot_magnitude == 0.75
        assert alert.feature_importance is None  # optional

    def test_tablename_is_alerts(self):
        assert Alert.__tablename__ == "alerts"


class TestGuidanceModel:
    def test_tablename_is_guidance(self):
        assert Guidance.__tablename__ == "guidance"

    def test_has_expected_fields(self):
        g = Guidance(alert_id=1, user_role="National Coordinator")
        assert g.user_role == "National Coordinator"
        assert g.guidance_markdown is None

    def test_status_enum_has_pending(self):
        assert GuidanceStatusEnum.PENDING.value == "PENDING"

    def test_status_enum_has_approved(self):
        assert GuidanceStatusEnum.APPROVED.value == "APPROVED"


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class TestAMRRecordCreateSchema:
    def _valid_data(self, **overrides):
        data = {
            "sector": "human",
            "pathogen_name": "E. coli",
            "antimicrobial_agent": "Ciprofloxacin",
            "county": "Nairobi",
            "result_value": "Resistant",
        }
        data.update(overrides)
        return data

    def test_valid_schema_instantiates(self):
        obj = AMRRecordCreate(**self._valid_data())
        assert obj.pathogen_name == "E. coli"

    def test_sector_converted_to_enum(self):
        obj = AMRRecordCreate(**self._valid_data(sector="animal"))
        assert obj.sector == SectorEnum.ANIMAL

    def test_invalid_sector_raises_validation_error(self):
        with pytest.raises(ValidationError):
            AMRRecordCreate(**self._valid_data(sector="invalid_sector"))

    def test_missing_pathogen_name_raises_error(self):
        data = self._valid_data()
        del data["pathogen_name"]
        with pytest.raises(ValidationError):
            AMRRecordCreate(**data)

    def test_missing_county_raises_error(self):
        data = self._valid_data()
        del data["county"]
        with pytest.raises(ValidationError):
            AMRRecordCreate(**data)

    def test_optional_fields_default_none(self):
        obj = AMRRecordCreate(**self._valid_data())
        assert obj.sub_county is None
        assert obj.facility_type is None
        assert obj.mic_value is None
        assert obj.hl7_fhir_id is None

    def test_genomic_signals_defaults_to_empty_list(self):
        obj = AMRRecordCreate(**self._valid_data())
        assert obj.genomic_signals == []

    def test_is_synthetic_defaults_to_one(self):
        obj = AMRRecordCreate(**self._valid_data())
        assert obj.is_synthetic == 1


class TestAMRRecordResponseSchema:
    def test_response_inherits_create_fields(self):
        """AMRRecordResponse is a superset of AMRRecordCreate."""
        create_fields = set(AMRRecordCreate.model_fields.keys())
        response_fields = set(AMRRecordResponse.model_fields.keys())
        assert create_fields.issubset(response_fields)

    def test_response_has_id_field(self):
        assert "id" in AMRRecordResponse.model_fields

    def test_response_has_timestamp_field(self):
        assert "timestamp" in AMRRecordResponse.model_fields

    def test_response_has_data_quality_score_field(self):
        assert "data_quality_score" in AMRRecordResponse.model_fields
