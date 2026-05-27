"""
test_cleaner.py — Unit tests for the DataCleaner service (Module 1).
"""

import pytest
import json
import pandas as pd
from src.services.ingestion.cleaner import DataCleaner


@pytest.fixture
def cleaner():
    return DataCleaner()


CLEAN_RECORD = {
    "sector": "human",
    "pathogen_name": "E. coli",
    "antimicrobial_agent": "Ciprofloxacin",
    "county": "Nairobi",
    "result_value": "Resistant",
    "facility_type": "Hospital",
}

MISSING_PATHOGEN = {
    "sector": "animal",
    "pathogen_name": None,
    "antimicrobial_agent": "Tetracycline",
    "county": "Kiambu",
    "result_value": "Sensitive",
    "facility_type": None,
}


class TestQualityScore:
    def test_perfect_record_scores_one(self, cleaner):
        clean, _ = cleaner.process_dirty_data([CLEAN_RECORD])
        assert clean[0]["data_quality_score"] == pytest.approx(1.0)

    def test_partial_record_scores_below_one(self, cleaner):
        record = CLEAN_RECORD.copy()
        record["facility_type"] = None
        clean, _ = cleaner.process_dirty_data([record])
        assert clean[0]["data_quality_score"] < 1.0


class TestCriticalFailures:
    def test_missing_pathogen_is_critical(self, cleaner):
        clean, failed = cleaner.process_dirty_data([CLEAN_RECORD, MISSING_PATHOGEN])
        assert len(failed) == 1
        assert pd.isnull(failed[0]["pathogen_name"])

    def test_clean_data_has_no_failures(self, cleaner):
        clean, failed = cleaner.process_dirty_data([CLEAN_RECORD])
        assert len(failed) == 0

    def test_missing_antimicrobial_is_critical(self, cleaner):
        record = CLEAN_RECORD.copy()
        record["antimicrobial_agent"] = None
        _, failed = cleaner.process_dirty_data([record])
        assert len(failed) == 1


class TestImputation:
    def test_missing_facility_type_imputed(self, cleaner):
        record = CLEAN_RECORD.copy()
        record["facility_type"] = None
        clean, _ = cleaner.process_dirty_data([record])
        assert clean[0]["facility_type"] == "Unknown/Not Reported"

    def test_sub_county_imputed_by_county_mode(self, cleaner):
        records = [
            {**CLEAN_RECORD, "sub_county": "Westlands"},
            {**CLEAN_RECORD, "sub_county": "Westlands"},
            {**CLEAN_RECORD, "sub_county": None},
        ]
        clean, _ = cleaner.process_dirty_data(records)
        assert clean[2]["sub_county"] == "Westlands"


class TestMissingFieldsTracking:
    def test_missing_fields_column_exists(self, cleaner):
        clean, _ = cleaner.process_dirty_data([CLEAN_RECORD])
        assert "missing_fields" in clean[0]

    def test_clean_record_has_empty_missing_fields(self, cleaner):
        clean, _ = cleaner.process_dirty_data([CLEAN_RECORD])
        assert json.loads(clean[0]["missing_fields"]) == []


class TestEdgeCases:
    def test_empty_payload_returns_empty_lists(self, cleaner):
        clean, failed = cleaner.process_dirty_data([])
        assert len(clean) == 0
        assert len(failed) == 0

    def test_returns_tuple_of_lists(self, cleaner):
        result = cleaner.process_dirty_data([CLEAN_RECORD])
        assert isinstance(result, tuple)
        assert isinstance(result[0], list)
        assert isinstance(result[1], list)
