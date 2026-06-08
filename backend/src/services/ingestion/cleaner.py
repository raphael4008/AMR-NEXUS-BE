# Track: backend/feature-api-name
# DataCleaner v1.3 — Vectorized data cleaning pipeline.
# Enforces Pydantic AMRRecordCreate validation BEFORE cleaning logic executes,
# preventing the validator bypass that was flagged in peer review.

import json
import logging
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any

import pandas as pd
from pydantic import ValidationError

logger = logging.getLogger(__name__)


# ── SIR normalization map (prevents CHAR(1) DB truncation) ────────────────────
_SIR_MAP: Dict[str, str] = {
    "resistant": "R",
    "susceptible": "S",
    "intermediate": "I",
    "sensitive": "S",
    "nonsusceptible": "R",
}

# ── Pathogen shorthand normalization (mirrors DB trigger for pre-DB safety) ────
_PATHOGEN_MAP: List[Tuple[Tuple[str, ...], str]] = [
    (("e. coli", "e coli"),             "Escherichia coli"),
    (("s. aureus", "s aureus"),         "Staphylococcus aureus"),
    (("k. pneumoniae", "k pneumoniae"), "Klebsiella pneumoniae"),
    (("a. baumannii", "a baumannii"),   "Acinetobacter baumannii"),
    (("p. aeruginosa", "p aeruginosa"), "Pseudomonas aeruginosa"),
    (("s. typhi", "s typhi"),           "Salmonella typhi"),
    (("s. enterica", "s enterica"),     "Salmonella enterica"),
    (("s. pneumoniae", "s pneumoniae"), "Streptococcus pneumoniae"),
]


def _normalize_pathogen(value: Any) -> Any:
    """Vectorized-friendly pathogen normalizer."""
    if not isinstance(value, str):
        return value
    vl = value.lower().strip()
    for shortcuts, canonical in _PATHOGEN_MAP:
        if any(s in vl for s in shortcuts):
            return canonical
    return value


def _normalize_sir(value: Any) -> Any:
    """Maps full-word SIR values to single CHAR(1) codes."""
    if pd.isna(value):
        return value
    mapped = _SIR_MAP.get(str(value).lower().strip())
    return mapped if mapped else value


class DataCleaner:
    """
    Pandas-driven data cleaner and group-mode imputation layer.
    Enforces Pydantic AMRRecordCreate validation loop BEFORE any
    data-cleaning or database-insertion blocks execute, closing
    the validator bypass identified in peer review.
    """

    CRITICAL_FIELDS = ["pathogen_name", "antibiotic_name", "sir_result", "county"]

    # Legacy field aliases from v1.2 that map to v1.3 column names
    _FIELD_ALIASES = {
        "antimicrobial_agent": "antibiotic_name",
        "result_value": "sir_result",
        "ncbi_tax_id": "ncbi_taxonomy_id",
    }

    def _apply_field_aliases(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transparently remap v1.2 legacy column names to v1.3 schema names.
        Allows existing upstream pipelines to continue working without modification.
        """
        for old_col, new_col in self._FIELD_ALIASES.items():
            if old_col in df.columns and new_col not in df.columns:
                df = df.rename(columns={old_col: new_col})
        return df

    def _pydantic_validation_pass(
        self, raw_records: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Runs each raw record dict through the Pydantic AMRRecordCreate schema
        BEFORE any pandas logic executes, enforcing GLASS compliance rules.

        Returns:
            - pydantic_valid: records that passed validation
            - pydantic_failed: records that failed, augmented with 'validation_error' key
        """
        # Inline import avoids circular dependency at module load time
        from src.schemas.backbone import AMRRecordCreate

        pydantic_valid: List[Dict[str, Any]] = []
        pydantic_failed: List[Dict[str, Any]] = []

        for record in raw_records:
            try:
                validated = AMRRecordCreate(**record)
                # Use model_dump to carry the normalized values forward
                pydantic_valid.append(validated.model_dump())
            except ValidationError as exc:
                failed_copy = dict(record)
                failed_copy["validation_error"] = exc.errors()
                pydantic_failed.append(failed_copy)

        return pydantic_valid, pydantic_failed

    def process_dirty_data(
        self, raw_payload: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Full pipeline:
        1. Alias v1.2 → v1.3 column names.
        2. Pydantic validation pass (GLASS compliance enforcement).
        3. Vectorized Pandas normalization and imputation on validated records.
        4. Isolate critical failures (missing non-negotiable fields).

        Returns:
            (clean_records, failed_records)
        """
        if not raw_payload:
            return [], []

        # ── Step 0: Normalize field aliases ───────────────────────────────────
        aliased_payload = []
        for rec in raw_payload:
            new_rec = dict(rec)
            for old_col, new_col in self._FIELD_ALIASES.items():
                if old_col in new_rec and new_col not in new_rec:
                    new_rec[new_col] = new_rec.pop(old_col)
            aliased_payload.append(new_rec)

        # ── Step 1: Pydantic validation loop (fixes validator bypass) ─────────
        pydantic_valid, pydantic_failed = self._pydantic_validation_pass(aliased_payload)

        if not pydantic_valid:
            return [], pydantic_failed

        # ── Step 2: Load validated records into DataFrame ─────────────────────
        df = pd.DataFrame(pydantic_valid)

        if df.empty:
            return [], pydantic_failed

        # ── Step 3: Calculate Data Quality Score (0.0–1.0) ───────────────────
        df["data_quality_score"] = (1.0 - df.isnull().mean(axis=1)).round(3)

        # ── Step 4: Track Missing Fields for Provenance (vectorized) ─────────
        null_mask = df.isnull()
        df["missing_fields"] = [
            json.dumps(null_mask.columns[mask].tolist())
            for mask in null_mask.to_numpy()
        ]

        # ── Step 5: SIR result normalization (CHAR(1) truncation guard) ──────
        if "sir_result" in df.columns:
            df["sir_result"] = df["sir_result"].apply(_normalize_sir)

        # ── Step 6: Pathogen name normalization (double safety after Pydantic) ─
        if "pathogen_name" in df.columns:
            df["pathogen_name"] = df["pathogen_name"].apply(_normalize_pathogen)

        # ── Step 7: Sub-county group-mode imputation ──────────────────────────
        if "sub_county" in df.columns and "county" in df.columns:
            county_modes = df.groupby("county")["sub_county"].agg(
                lambda x: x.mode().iloc[0] if not x.mode().empty else "Unknown"
            )
            df["sub_county"] = df["sub_county"].fillna(df["county"].map(county_modes))
            df["sub_county"] = df["sub_county"].fillna("Unknown")

        # ── Step 8: Facility type imputation ─────────────────────────────────
        if "facility_type" in df.columns:
            df["facility_type"] = df["facility_type"].fillna("Unknown/Not Reported")

        # ── Step 9: Set default sample_collection_date if missing ─────────────
        now_utc = datetime.now(timezone.utc)
        if "sample_collection_date" not in df.columns:
            df["sample_collection_date"] = now_utc
        else:
            df["sample_collection_date"] = df["sample_collection_date"].fillna(now_utc)

        # ── Step 10: Ensure all critical fields exist ─────────────────────────
        for col in self.CRITICAL_FIELDS:
            if col not in df.columns:
                df[col] = None

        # ── Step 11: Isolate hard-critical failures ───────────────────────────
        critical_null_mask = df[self.CRITICAL_FIELDS].isnull().any(axis=1)
        rejected_df = df[critical_null_mask]
        clean_df = df[~critical_null_mask]

        # ── Merge failed records from both validation stages ──────────────────
        all_failed = pydantic_failed + rejected_df.to_dict(orient="records")

        return clean_df.to_dict(orient="records"), all_failed
