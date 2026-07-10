"""
Feature Engineering Pipeline — AMR-Nexus One Health Intelligence
================================================================
Stateless feature computation for AMR surveillance data.
Converts raw AMR records into standardised feature DataFrames consumed by
XGBoost, Isolation Forest, and Prophet models.

Feature Groups:
    1. Base resistance rates per (year_month, pathogen, drug_class, county)
    2. Rolling resistance rates (3/6/12-month windows)
    3. MDR prevalence rate per county per month
    4. Reporting lag statistics (mean, median, p95)
    5. Seasonal decomposition (month-of-year, quarter, sin/cos encoding)
    6. Cross-sector resistance correlation
    7. Geographic clustering (neighbouring county rates)
    8. Rate-of-change (month-over-month delta and pct_change)
    9. Prior antibiotic exposure rate (proxy for antibiotic-use pressure —
       real per-record signal, not a substitute for prescription/dispensing
       volume data, which this dataset does not contain)

Column Naming Convention:
    ``{metric}_{window}_{grouping}``
    e.g. ``resistance_rate_rolling_6m``, ``mdr_prevalence_county``

Grouping Key:
    ``(year_month, pathogen_name, drug_class, county_code)``

Supported Record Formats:
    - **Nested**:  ``record['pathogen']['organism_name']``,
      ``record['geography']['county_code']``
    - **Flat schema**: ``record['pathogen_name']``, ``record['county_code']``
    - **AMR-Nexus backend** (Raph's ingestion):
      ``record['pathogen_name']``, ``record['antimicrobial_agent']``,
      ``record['county']``, ``record['result_value']``
      (Resistant/Intermediate/Sensitive), ``record['sector']``,
      ``record['timestamp']``
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from ml_ai.config import get_ml_config

logger = logging.getLogger(__name__)

# ============================================================================
# KENYA COUNTY REFERENCE — all 47 counties
# ============================================================================

KENYA_COUNTIES: Dict[str, str] = {
    "001": "Mombasa",
    "002": "Kwale",
    "003": "Kilifi",
    "004": "Tana River",
    "005": "Lamu",
    "006": "Taita Taveta",
    "007": "Garissa",
    "008": "Wajir",
    "009": "Mandera",
    "010": "Marsabit",
    "011": "Isiolo",
    "012": "Meru",
    "013": "Tharaka Nithi",
    "014": "Embu",
    "015": "Kitui",
    "016": "Machakos",
    "017": "Makueni",
    "018": "Nyandarua",
    "019": "Nyeri",
    "020": "Kirinyaga",
    "021": "Murang'a",
    "022": "Kiambu",
    "023": "Turkana",
    "024": "West Pokot",
    "025": "Samburu",
    "026": "Trans Nzoia",
    "027": "Uasin Gishu",
    "028": "Elgeyo Marakwet",
    "029": "Nandi",
    "030": "Baringo",
    "031": "Laikipia",
    "032": "Nakuru",
    "033": "Narok",
    "034": "Kajiado",
    "035": "Kericho",
    "036": "Bomet",
    "037": "Kakamega",
    "038": "Vihiga",
    "039": "Bungoma",
    "040": "Busia",
    "041": "Siaya",
    "042": "Kisumu",
    "043": "Homa Bay",
    "044": "Migori",
    "045": "Kisii",
    "046": "Nyamira",
    "047": "Nairobi",
}

# ============================================================================
# KENYA COUNTY ADJACENCY GRAPH — for geographic clustering features
# Simplified adjacency: maps county code → list of neighbouring county codes
# ============================================================================

COUNTY_ADJACENCY: Dict[str, List[str]] = {
    "001": ["002", "003"],                              # Mombasa → Kwale, Kilifi
    "002": ["001", "003", "006"],                        # Kwale
    "003": ["001", "002", "004", "005"],                 # Kilifi
    "004": ["003", "005", "007", "015"],                 # Tana River
    "005": ["003", "004"],                               # Lamu
    "006": ["002", "016", "034"],                        # Taita Taveta
    "007": ["004", "008", "011", "015"],                 # Garissa
    "008": ["007", "009", "010"],                        # Wajir
    "009": ["008", "010"],                               # Mandera
    "010": ["008", "009", "011", "023", "025"],           # Marsabit
    "011": ["007", "010", "012", "025", "031"],           # Isiolo
    "012": ["011", "013", "014", "031"],                  # Meru
    "013": ["012", "014", "015"],                         # Tharaka Nithi
    "014": ["012", "013", "015", "020"],                  # Embu
    "015": ["004", "007", "013", "014", "016"],           # Kitui
    "016": ["006", "015", "017", "034"],                  # Machakos
    "017": ["016", "034"],                               # Makueni
    "018": ["019", "022", "032"],                         # Nyandarua
    "019": ["012", "018", "020", "022", "031"],           # Nyeri
    "020": ["014", "019", "021"],                         # Kirinyaga
    "021": ["019", "020", "022"],                         # Murang'a
    "022": ["018", "019", "021", "032", "047"],           # Kiambu
    "023": ["010", "024", "025"],                         # Turkana
    "024": ["023", "026", "028", "029"],                  # West Pokot
    "025": ["010", "011", "023", "030", "031"],           # Samburu
    "026": ["024", "027", "039"],                         # Trans Nzoia
    "027": ["026", "028", "029", "032"],                  # Uasin Gishu
    "028": ["024", "027", "029", "030"],                  # Elgeyo Marakwet
    "029": ["024", "027", "028", "035"],                  # Nandi
    "030": ["025", "028", "031", "032"],                  # Baringo
    "031": ["011", "012", "019", "025", "030", "032"],    # Laikipia
    "032": ["018", "022", "027", "030", "031", "033", "035"],  # Nakuru
    "033": ["032", "034", "036"],                         # Narok
    "034": ["006", "016", "017", "033", "047"],           # Kajiado
    "035": ["029", "032", "036", "046"],                  # Kericho
    "036": ["033", "035", "045"],                         # Bomet
    "037": ["038", "039", "040", "041"],                  # Kakamega
    "038": ["037", "041", "042", "046"],                  # Vihiga
    "039": ["026", "037", "040"],                         # Bungoma
    "040": ["037", "039", "041"],                         # Busia
    "041": ["037", "038", "040", "042", "043"],           # Siaya
    "042": ["038", "041", "043", "046"],                  # Kisumu
    "043": ["041", "042", "044"],                         # Homa Bay
    "044": ["043", "045"],                               # Migori
    "045": ["036", "044", "046"],                         # Kisii
    "046": ["035", "038", "042", "045"],                  # Nyamira
    "047": ["022", "016", "034"],                         # Nairobi
}

# ============================================================================
# DEFAULT DRUG CLASSES — used when all_drug_classes is not populated from data
# ============================================================================

_DEFAULT_DRUG_CLASSES: Set[str] = {
    "Penicillins",
    "Cephalosporins",
    "Carbapenems",
    "Fluoroquinolones",
    "Aminoglycosides",
    "Tetracyclines",
    "Macrolides",
    "Sulfonamides",
    "Glycopeptides",
    "Polymyxins",
    "Oxazolidinones",
    "Nitrofurans",
    "Rifamycins",
    "Lincosamides",
    "Chloramphenicol",
}

# ============================================================================
# RESULT VALUE → RESISTANCE MAPPING for AMR-Nexus backend records
# ============================================================================

_RESULT_VALUE_MAP: Dict[str, str] = {
    "resistant": "R",
    "r": "R",
    "intermediate": "I",
    "i": "I",
    "sensitive": "S",
    "susceptible": "S",
    "s": "S",
}


# ============================================================================
# FEATURE METADATA
# ============================================================================

@dataclass
class FeatureMetadata:
    """Metadata about a computed feature DataFrame.

    Attributes:
        feature_count: Number of numeric feature columns produced.
        record_count: Number of rows in the feature DataFrame.
        date_range: Tuple of (earliest_date, latest_date) in the data.
        pathogens: List of unique pathogens represented.
        drug_classes: List of unique drug classes represented.
        counties: List of unique county codes represented.
        computation_time_seconds: Wall-clock time for feature computation.
    """

    feature_count: int = 0
    record_count: int = 0
    date_range: Tuple[date, date] = field(
        default_factory=lambda: (date.today(), date.today())
    )
    pathogens: List[str] = field(default_factory=list)
    drug_classes: List[str] = field(default_factory=list)
    counties: List[str] = field(default_factory=list)
    computation_time_seconds: float = 0.0


# ============================================================================
# FEATURE ENGINEER
# ============================================================================

class FeatureEngineer:
    """Stateless feature engineering pipeline for AMR surveillance data.

    Converts raw AMR records (dicts or DataFrames) into standardised feature
    matrices suitable for anomaly detection and forecasting models.

    The pipeline is **stateless** and deterministic — given the same input data
    and target date, it produces identical output.  No model artefacts are
    stored.

    Supports three record formats:
        1. **Nested schema**: ``record['pathogen']['organism_name']``,
           ``record['geography']['county_code']``
        2. **Flat schema**: ``record['pathogen_name']``,
           ``record['county_code']``
        3. **AMR-Nexus backend** (Raph/Naomi ingestion):
           ``record['pathogen_name']``, ``record['antimicrobial_agent']``,
           ``record['county']``, ``record['result_value']``
           (Resistant/Intermediate/Sensitive), ``record['sector']``,
           ``record['timestamp']``

    Attributes:
        adjacency: County adjacency graph for geographic clustering.
        all_drug_classes: Set of all known drug classes.
        metadata: FeatureMetadata from the most recent computation.
    """

    def __init__(self) -> None:
        """Initialise FeatureEngineer with county adjacency and drug classes."""
        self.adjacency: Dict[str, List[str]] = COUNTY_ADJACENCY
        self.all_drug_classes: Set[str] = set(_DEFAULT_DRUG_CLASSES)
        self.metadata: Optional[FeatureMetadata] = None
        self._config = get_ml_config()
        logger.info(
            "FeatureEngineer initialised with %d counties, %d drug classes",
            len(KENYA_COUNTIES),
            len(self.all_drug_classes),
        )

    # ------------------------------------------------------------------ #
    # PUBLIC API                                                          #
    # ------------------------------------------------------------------ #

    def build_training_features(
        self,
        records: List[dict],
        target_date_range: Tuple[date, date],
    ) -> pd.DataFrame:
        """Build feature matrix for model training.

        Args:
            records: Raw AMR records as dicts (flat, nested, or backend format).
            target_date_range: ``(start_date, end_date)`` inclusive window for
                the training period.

        Returns:
            Feature DataFrame indexed by
            ``(year_month, pathogen_name, drug_class, county_code)`` with all
            engineered features.  Returns an empty DataFrame when no records
            fall within the requested date range.
        """
        t0 = time.perf_counter()
        logger.info(
            "Building training features — %d records, range %s",
            len(records),
            target_date_range,
        )

        df = self._records_to_dataframe(records)
        df = self._filter_date_range(df, target_date_range[0], target_date_range[1])

        if df.empty:
            logger.warning("No records found in date range %s", target_date_range)
            return pd.DataFrame()

        features = self._compute_all_features(df)
        elapsed = time.perf_counter() - t0

        self._build_metadata(features, elapsed)
        logger.info(
            "Training features built — shape=%s, elapsed=%.2fs",
            features.shape,
            elapsed,
        )
        return features

    def build_inference_features(
        self,
        records: List[dict],
        as_of_date: date,
    ) -> pd.DataFrame:
        """Build feature matrix for real-time inference.

        Uses only data available up to ``as_of_date`` to prevent data leakage.
        Returns features for the most recent month only.

        Args:
            records: Raw AMR records as dicts.
            as_of_date: Point-in-time cutoff for feature computation.  Only
                data collected on or before this date is used.

        Returns:
            Feature DataFrame containing the most recent month's features.
            Returns an empty DataFrame when no usable records exist.
        """
        t0 = time.perf_counter()
        logger.info(
            "Building inference features — %d records, as_of_date=%s",
            len(records),
            as_of_date,
        )

        df = self._records_to_dataframe(records)
        # Look back up to 12 months for rolling features but never beyond
        # as_of_date to prevent leakage.
        cutoff_start = as_of_date - timedelta(days=365)
        df = self._filter_date_range(df, cutoff_start, as_of_date)

        if df.empty:
            logger.warning("No records found before as_of_date=%s", as_of_date)
            return pd.DataFrame()

        features = self._compute_all_features(df)

        # Keep only the most recent month for inference
        #if "year_month" in features.columns and not features.empty:
        #   latest_month = features["year_month"].max()
        #    features = features[features["year_month"] == latest_month].copy()

        # REPLACE WITH — keep all months, log how many we're scoring:
        # Return features for ALL months (batch ingest mode)
        # The most-recent-month filter is intentionally removed here so that
        # a full historical ingest generates alerts across the entire dataset.
        # For real-time single-record inference, the caller passes only recent
        # records so the scope is naturally limited.
        if "year_month" in features.columns and not features.empty:
            logger.info(
                "Inference features cover %d months (%s → %s)",
                features["year_month"].nunique(),
                features["year_month"].min(),
                features["year_month"].max(),
            )

        elapsed = time.perf_counter() - t0

        self._build_metadata(features, elapsed)
        logger.info(
            "Inference features built — shape=%s, elapsed=%.2fs",
            features.shape,
            elapsed,
        )
        return features

    # ------------------------------------------------------------------ #
    # DATA PREPARATION                                                    #
    # ------------------------------------------------------------------ #

    def _records_to_dataframe(self, records: List[dict]) -> pd.DataFrame:
        """Flatten raw AMR records into a tabular DataFrame.

        Handles three input formats:
            1. Nested schema with ``pathogen``, ``geography``, ``timestamps``
               sub-dicts and a ``resistance_results`` list.
            2. Pre-flattened dicts with top-level keys.
            3. AMR-Nexus backend format with ``result_value``,
               ``antimicrobial_agent``, ``county``, ``timestamp``.

        Args:
            records: List of raw record dictionaries.

        Returns:
            DataFrame with one row per drug-test observation.
        """
        rows: List[Dict[str, Any]] = []
        for rec in records:
            try:
                base = self._extract_base_fields(rec)
                # Explode resistance results — one row per drug test
                rr_list = rec.get("resistance_results", [])
                if isinstance(rr_list, list) and len(rr_list) > 0:
                    for rr in rr_list:
                        row = {**base, **self._extract_resistance_fields(rr)}
                        rows.append(row)
                else:
                    # Backend format or flat record without resistance_results
                    row = {**base, **self._extract_resistance_from_flat(rec)}
                    rows.append(row)
            except Exception:
                logger.debug("Skipping malformed record: %s", rec.get("id", "?"), exc_info=True)
                continue

        df = pd.DataFrame(rows)
        if df.empty:
            logger.warning("No rows produced from %d input records", len(records))
            return df

        # Ensure date column is date type
        if "sample_collection_date" in df.columns:
            df["sample_collection_date"] = pd.to_datetime(
                df["sample_collection_date"], errors="coerce"
            ).dt.date

        # Drop rows with unparseable dates
        df = df.dropna(subset=["sample_collection_date"])
        if df.empty:
            return df

        # Year-month period for grouping
        df["year_month"] = pd.to_datetime(
            df["sample_collection_date"]
        ).dt.to_period("M")

        # Ensure is_resistant is present and numeric
        if "is_resistant" in df.columns:
            df["is_resistant"] = pd.to_numeric(df["is_resistant"], errors="coerce").fillna(0).astype(int)

        # Track discovered drug classes
        if "drug_class" in df.columns:
            discovered = set(df["drug_class"].dropna().unique()) - {"Unknown", ""}
            if discovered:
                self.all_drug_classes |= discovered

        return df

    def _extract_base_fields(self, rec: dict) -> Dict[str, Any]:
        """Extract common fields from a record, handling nested vs flat vs backend.

        Args:
            rec: A single raw AMR record dictionary.

        Returns:
            Dictionary of normalised base fields.
        """
        # --- Pathogen ---
        pathogen = rec.get("pathogen", {})
        if isinstance(pathogen, dict) and pathogen:
            pathogen_name = pathogen.get("organism_name", "Unknown")
            pathogen_ncbi_id = pathogen.get("ncbi_taxonomy_id", 0)
        else:
            pathogen_name = rec.get("pathogen_name", "Unknown")
            pathogen_ncbi_id = rec.get("ncbi_tax_id", rec.get("pathogen_ncbi_id", 0))

        # --- Geography ---
        geo = rec.get("geography", {})
        if isinstance(geo, dict) and geo:
            county_code = geo.get("county_code", "000")
            county_name = geo.get("county_name", "Unknown")
            sub_county = geo.get("sub_county", "Unknown")
        else:
            # AMR-Nexus backend uses 'county' as the county code
            county_code = rec.get("county_code", rec.get("county", "000"))
            county_name = rec.get(
                "county_name",
                KENYA_COUNTIES.get(str(county_code).zfill(3), "Unknown"),
            )
            sub_county = rec.get("sub_county", "Unknown")

        # Normalise county_code to zero-padded 3-digit string
        county_code = str(county_code).zfill(3)

        # --- Timestamps ---
        ts = rec.get("timestamps", {})
        if isinstance(ts, dict) and ts:
            collection_date = ts.get("sample_collection_date")
            report_date = ts.get("lab_report_date")
            lag = ts.get("reporting_lag_days")
        else:
            # AMR-Nexus backend uses 'timestamp' as the collection date
            collection_date = rec.get(
                "sample_collection_date",
                rec.get("timestamp", rec.get("collection_date")),
            )
            report_date = rec.get("lab_report_date")
            lag = rec.get("reporting_lag_days")

        # --- Compute lag if we have both dates and lag is missing ---
        if lag is None and collection_date is not None and report_date is not None:
            try:
                cd = pd.to_datetime(collection_date)
                rd = pd.to_datetime(report_date)
                lag = (rd - cd).days
            except Exception:
                lag = None

        # --- Sector ---
        sector = rec.get("sector", "human")

        # --- MDR flags ---
        mdr_flag = rec.get("mdr_flag", False)
        resistant_class_count = rec.get("resistant_class_count", 0)

        # --- Prior antibiotic exposure (real per-record signal, proxy for
        # antibiotic-use pressure) ---
        # Stored as True/False/None on AMRRecord (None = "Unknown"/"Not
        # applicable" in the source data). Left as-is here — aggregation
        # decides how to handle the None case, not extraction.
        prior_antibiotic_exposure = rec.get("prior_antibiotic_exposure")

        return {
            "record_id": rec.get("record_id", rec.get("id", "")),
            "sector": sector,
            "pathogen_name": pathogen_name,
            "pathogen_ncbi_id": pathogen_ncbi_id,
            "county_code": county_code,
            "county_name": county_name,
            "sub_county": sub_county,
            "sample_collection_date": collection_date,
            "lab_report_date": report_date,
            "reporting_lag_days": lag,
            "mdr_flag": mdr_flag,
            "resistant_class_count": resistant_class_count,
            "prior_antibiotic_exposure": prior_antibiotic_exposure,
            "data_quality_score": rec.get("data_quality_score", 1.0),
        }

    def _extract_resistance_fields(self, rr: dict) -> Dict[str, Any]:
        """Extract resistance result fields from a single nested test result.

        Args:
            rr: A single resistance result dictionary, potentially containing
                an ``antimicrobial`` sub-dict.

        Returns:
            Dictionary with drug_class, drug_name, sir, is_resistant, etc.
        """
        am = rr.get("antimicrobial", rr)
        if isinstance(am, dict):
            drug_class = am.get("drug_class", "Unknown")
            drug_name = am.get("name", am.get("drug_name", "Unknown"))
            aware_class = am.get("aware_class", "Unknown")
            atc_code = am.get("atc_code", "")
        else:
            drug_class = rr.get("drug_class", "Unknown")
            drug_name = rr.get("drug_name", "Unknown")
            aware_class = rr.get("aware_class", "Unknown")
            atc_code = rr.get("atc_code", "")

        sir = rr.get("susceptibility", rr.get("sir", "U"))
        is_resistant = 1 if str(sir).upper() == "R" else 0

        return {
            "drug_class": drug_class,
            "drug_name": drug_name,
            "aware_class": aware_class,
            "atc_code": atc_code,
            "sir": sir,
            "is_resistant": is_resistant,
            "mic_value": rr.get("mic_value"),
        }

    def _extract_resistance_from_flat(self, rec: dict) -> Dict[str, Any]:
        """Extract resistance fields from a flat / AMR-Nexus backend record.

        Handles the ``result_value`` (Resistant/Intermediate/Sensitive) and
        ``antimicrobial_agent`` fields used by the AMR-Nexus backend.

        Args:
            rec: A flat AMR record dictionary.

        Returns:
            Dictionary with drug_class, drug_name, sir, is_resistant, etc.
        """
        # Drug info — backend uses 'antimicrobial_agent', flat uses 'drug_name'
        drug_name = rec.get(
            "antimicrobial_agent",
            rec.get("drug_name", "Unknown"),
        )
        drug_class = rec.get("drug_class", "Unknown")
        aware_class = rec.get("aware_class", "Unknown")
        atc_code = rec.get("atc_code", "")

        # SIR from result_value (Resistant/Intermediate/Sensitive) or sir field
        result_value = rec.get("result_value", rec.get("sir", "U"))
        sir = _RESULT_VALUE_MAP.get(str(result_value).lower().strip(), str(result_value).upper()[:1])
        is_resistant = 1 if sir == "R" else 0

        return {
            "drug_class": drug_class,
            "drug_name": drug_name,
            "aware_class": aware_class,
            "atc_code": atc_code,
            "sir": sir,
            "is_resistant": is_resistant,
            "mic_value": rec.get("mic_value"),
        }

    def _filter_date_range(
        self, df: pd.DataFrame, start: date, end: date
    ) -> pd.DataFrame:
        """Filter DataFrame to records within the date range (inclusive).

        Args:
            df: Input DataFrame with ``sample_collection_date`` column.
            start: Start date (inclusive).
            end: End date (inclusive).

        Returns:
            Filtered copy of the DataFrame.
        """
        if df.empty or "sample_collection_date" not in df.columns:
            return df
        mask = (df["sample_collection_date"] >= start) & (
            df["sample_collection_date"] <= end
        )
        filtered = df[mask].copy()
        logger.debug(
            "Date filter %s–%s: %d → %d rows",
            start, end, len(df), len(filtered),
        )
        return filtered

    # ------------------------------------------------------------------ #
    # FEATURE COMPUTATION PIPELINE                                        #
    # ------------------------------------------------------------------ #

    def _compute_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Orchestrate all feature groups and merge into a single DataFrame.

        Each feature group is computed independently and merged on the
        canonical grouping key:
        ``(year_month, pathogen_name, drug_class, county_code)``.

        Args:
            df: Prepared DataFrame from ``_records_to_dataframe``.

        Returns:
            Merged feature DataFrame with all engineered features.
        """
        group_cols = ["year_month", "pathogen_name", "drug_class", "county_code"]

        # 1. Base aggregation — resistance rates per group
        base = self._compute_base_resistance(df, group_cols)
        if base.empty:
            logger.warning("Base resistance computation returned empty DataFrame")
            return base

        # 2. Rolling resistance rates
        rolling = self._compute_rolling_resistance(base, group_cols)

        # 3. MDR prevalence
        mdr = self._compute_mdr_prevalence(df)

        # 4. Reporting lag statistics
        lag = self._compute_reporting_lag_stats(df)

        # 5. Seasonal features
        seasonal = self._compute_seasonal_features(base)

        # 6. Cross-sector correlation features
        cross_sector = self._compute_cross_sector_features(df, group_cols)

        # 7. Geographic clustering features
        geo = self._compute_geographic_clustering(base, group_cols)

        # 8. Rate-of-change features
        roc = self._compute_rate_of_change(base, group_cols)

        # 9. Prior antibiotic exposure rate (proxy for antibiotic-use
        # pressure — see _compute_prior_exposure_rate docstring for what
        # this is and isn't)
        exposure = self._compute_prior_exposure_rate(df)

        # --- Merge all feature groups ---
        features = base.copy()

        # Merge features keyed on full group_cols
        for feat_df in [rolling, seasonal, roc, exposure]:
            if feat_df is not None and not feat_df.empty:
                features = features.merge(
                    feat_df, on=group_cols, how="left", suffixes=("", "_dup")
                )
                features = features.loc[
                    :, ~features.columns.str.endswith("_dup")
                ]

        # Merge MDR (keyed on year_month + county_code)
        if mdr is not None and not mdr.empty:
            features = features.merge(
                mdr,
                on=["year_month", "county_code"],
                how="left",
                suffixes=("", "_dup"),
            )
            features = features.loc[:, ~features.columns.str.endswith("_dup")]

        # Merge lag (keyed on year_month + county_code)
        if lag is not None and not lag.empty:
            features = features.merge(
                lag,
                on=["year_month", "county_code"],
                how="left",
                suffixes=("", "_dup"),
            )
            features = features.loc[:, ~features.columns.str.endswith("_dup")]

        # Merge cross-sector (keyed on full group_cols)
        if cross_sector is not None and not cross_sector.empty:
            features = features.merge(
                cross_sector,
                on=group_cols,
                how="left",
                suffixes=("", "_dup"),
            )
            features = features.loc[:, ~features.columns.str.endswith("_dup")]

        # Merge geographic clustering (keyed on full group_cols)
        if geo is not None and not geo.empty:
            features = features.merge(
                geo,
                on=group_cols,
                how="left",
                suffixes=("", "_dup"),
            )
            features = features.loc[:, ~features.columns.str.endswith("_dup")]

        # Fill NaN with 0 for numeric columns
        numeric_cols = features.select_dtypes(include=[np.number]).columns
        features[numeric_cols] = features[numeric_cols].fillna(0.0)

        logger.info("All features computed — shape=%s", features.shape)
        return features

    # ------------------------------------------------------------------ #
    # 1. BASE RESISTANCE RATES                                            #
    # ------------------------------------------------------------------ #

    def _compute_base_resistance(
        self, df: pd.DataFrame, group_cols: List[str]
    ) -> pd.DataFrame:
        """Compute resistance rate per (year_month, pathogen, drug_class, county).

        Args:
            df: Prepared DataFrame with ``is_resistant`` column.
            group_cols: Columns to group by.

        Returns:
            DataFrame with columns: ``group_cols`` +
            ``[resistance_rate, total_tests, resistant_count, county_name,
            sub_county, sector]``.
        """
        working = df.copy()

        if "is_resistant" not in working.columns:
            if "sir" in working.columns:
                working["is_resistant"] = (working["sir"].astype(str).str.upper() == "R").astype(int)
            else:
                logger.warning("Neither 'is_resistant' nor 'sir' column found — defaulting to 0")
                working["is_resistant"] = 0

        # Ensure grouping columns exist with fallbacks
        for col, default in [
            ("county_name", "Unknown"),
            ("sub_county", "Unknown"),
            ("sector", "human"),
        ]:
            if col not in working.columns:
                working[col] = default

        try:
            agg = (
                working.groupby(group_cols, observed=True)
                .agg(
                    resistance_rate=("is_resistant", "mean"),
                    total_tests=("is_resistant", "count"),
                    resistant_count=("is_resistant", "sum"),
                    county_name=("county_name", "first"),
                    sub_county=("sub_county", "first"),
                    sector=("sector", "first"),
                )
                .reset_index()
            )
        except Exception:
            logger.exception("Failed to compute base resistance aggregation")
            return pd.DataFrame()

        logger.debug("Base resistance: %d groups from %d rows", len(agg), len(working))
        return agg

    # ------------------------------------------------------------------ #
    # 2. ROLLING RESISTANCE RATES                                         #
    # ------------------------------------------------------------------ #

    def _compute_rolling_resistance(
        self, base: pd.DataFrame, group_cols: List[str]
    ) -> pd.DataFrame:
        """Compute rolling mean resistance rates over 3, 6, and 12-month windows.

        The rolling window is applied per
        ``(pathogen_name, drug_class, county_code)`` sorted by ``year_month``.

        Args:
            base: Base resistance DataFrame from ``_compute_base_resistance``.
            group_cols: Full grouping columns list.

        Returns:
            DataFrame with columns: ``group_cols`` +
            ``[resistance_rate_rolling_3m, resistance_rate_rolling_6m,
            resistance_rate_rolling_12m]``.
        """
        entity_cols = ["pathogen_name", "drug_class", "county_code"]
        base_sorted = base.sort_values(group_cols)

        results: List[pd.DataFrame] = []
        for _, group in base_sorted.groupby(entity_cols, observed=True):
            g = group.copy()
            for window_months, col_name in [
                (3, "resistance_rate_rolling_3m"),
                (6, "resistance_rate_rolling_6m"),
                (12, "resistance_rate_rolling_12m"),
            ]:
                g[col_name] = (
                    g["resistance_rate"]
                    .rolling(window=window_months, min_periods=1)
                    .mean()
                )
            results.append(
                g[
                    group_cols
                    + [
                        "resistance_rate_rolling_3m",
                        "resistance_rate_rolling_6m",
                        "resistance_rate_rolling_12m",
                    ]
                ]
            )

        if not results:
            return pd.DataFrame()

        return pd.concat(results, ignore_index=True)

    # ------------------------------------------------------------------ #
    # 3. MDR PREVALENCE                                                   #
    # ------------------------------------------------------------------ #

    def _compute_mdr_prevalence(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute multi-drug resistance prevalence rate per county per month.

        MDR is defined as resistance to ≥3 antimicrobial classes. The
        ``mdr_flag`` field should be pre-computed on the source record.

        Args:
            df: Prepared DataFrame with ``mdr_flag`` column.

        Returns:
            DataFrame with columns:
            ``[year_month, county_code, mdr_prevalence_county, mdr_count,
            total_records]``.
        """
        if "mdr_flag" not in df.columns:
            logger.debug("No mdr_flag column — skipping MDR prevalence")
            return pd.DataFrame()

        # Deduplicate to record level (a record may have multiple drug rows)
        id_cols = ["record_id", "year_month", "county_code"]
        available_id_cols = [c for c in id_cols if c in df.columns]
        if len(available_id_cols) < 2:
            logger.debug("Insufficient ID columns for MDR deduplication")
            return pd.DataFrame()

        records = df.drop_duplicates(subset=available_id_cols)

        try:
            mdr = (
                records.groupby(["year_month", "county_code"], observed=True)
                .agg(
                    mdr_prevalence_county=("mdr_flag", "mean"),
                    mdr_count=("mdr_flag", "sum"),
                    total_records=("mdr_flag", "count"),
                )
                .reset_index()
            )
        except Exception:
            logger.exception("Failed to compute MDR prevalence")
            return pd.DataFrame()

        return mdr

    # ------------------------------------------------------------------ #
    # 4. REPORTING LAG STATISTICS                                         #
    # ------------------------------------------------------------------ #

    def _compute_reporting_lag_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute reporting lag statistics per county per month.

        Metrics produced:
            - ``reporting_lag_mean``: mean lag in days
            - ``reporting_lag_median``: median lag in days
            - ``reporting_lag_p95``: 95th-percentile lag in days

        Args:
            df: Prepared DataFrame with ``reporting_lag_days`` column.

        Returns:
            DataFrame with lag statistics, or empty DataFrame if no lag data
            is available.
        """
        if "reporting_lag_days" not in df.columns:
            logger.debug("No reporting_lag_days column — skipping lag stats")
            return pd.DataFrame()

        lag_df = df.dropna(subset=["reporting_lag_days"]).copy()
        if lag_df.empty:
            logger.debug("All reporting_lag_days are NaN — skipping lag stats")
            return pd.DataFrame()

        lag_df["reporting_lag_days"] = pd.to_numeric(
            lag_df["reporting_lag_days"], errors="coerce"
        )
        lag_df = lag_df.dropna(subset=["reporting_lag_days"])
        if lag_df.empty:
            return pd.DataFrame()

        try:
            stats = (
                lag_df.groupby(
                    ["year_month", "county_code"], observed=True
                )["reporting_lag_days"]
                .agg(
                    reporting_lag_mean="mean",
                    reporting_lag_median="median",
                    reporting_lag_p95=lambda x: (
                        np.percentile(x, 95) if len(x) > 0 else 0.0
                    ),
                )
                .reset_index()
            )
        except Exception:
            logger.exception("Failed to compute reporting lag stats")
            return pd.DataFrame()

        return stats

    # ------------------------------------------------------------------ #
    # 5. SEASONAL FEATURES                                                #
    # ------------------------------------------------------------------ #

    def _compute_seasonal_features(self, base: pd.DataFrame) -> pd.DataFrame:
        """Add seasonal decomposition features.

        Produces:
            - ``month_of_year``: integer 1–12
            - ``quarter``: integer 1–4
            - ``month_sin``: sine cyclical encoding (period 12)
            - ``month_cos``: cosine cyclical encoding (period 12)

        Args:
            base: Base resistance DataFrame.

        Returns:
            DataFrame with seasonal columns keyed on ``group_cols``.
        """
        group_cols = ["year_month", "pathogen_name", "drug_class", "county_code"]
        feat = base[group_cols].copy()

        feat["month_of_year"] = feat["year_month"].apply(lambda p: p.month)
        feat["quarter"] = feat["year_month"].apply(
            lambda p: (p.month - 1) // 3 + 1
        )
        # Cyclical encoding so January and December are close
        feat["month_sin"] = feat["month_of_year"].apply(
            lambda m: math.sin(2 * math.pi * m / 12)
        )
        feat["month_cos"] = feat["month_of_year"].apply(
            lambda m: math.cos(2 * math.pi * m / 12)
        )

        return feat

    # ------------------------------------------------------------------ #
    # 6. CROSS-SECTOR CORRELATION                                         #
    # ------------------------------------------------------------------ #

    _SECTOR_CATEGORIES = ["HUMAN", "ANIMAL", "ENVIRONMENT"]

    def _compute_cross_sector_features(self, df, group_cols):
        """Compute cross-sector resistance correlation features.

        Always emits all three ``resistance_rate_{sector}_sector`` columns,
        regardless of which sectors are present in the current batch, so the
        feature schema is identical between training and inference. Missing
        sectors are filled with 0.0 (no cross-sector signal available).
        """
        if "sector" not in df.columns or "is_resistant" not in df.columns:
            return pd.DataFrame()
        try:
            sector_rates = (
                df.groupby(
                    ["year_month", "pathogen_name", "drug_class", "county_code", "sector"],
                    observed=True
                )["is_resistant"]
                .mean()
                .reset_index()
                .rename(columns={"is_resistant": "sector_resistance_rate"})
            )
            pivoted = sector_rates.pivot_table(
                index=["year_month", "pathogen_name", "drug_class", "county_code"],
                columns="sector",
                values="sector_resistance_rate",
            )
            # Always reindex to the full canonical sector list so training and
            # inference produce an IDENTICAL schema no matter which sectors
            # happen to appear in a given batch.
            pivoted = pivoted.reindex(columns=self._SECTOR_CATEGORIES, fill_value=0.0)
            pivoted = pivoted.reset_index()
            pivoted = pivoted.rename(columns={s: f"resistance_rate_{s}_sector" for s in self._SECTOR_CATEGORIES})
        except Exception:
            logger.exception("Failed to compute cross-sector features")
            return pd.DataFrame()
        return pivoted

    # ------------------------------------------------------------------ #
    # 9. PRIOR ANTIBIOTIC EXPOSURE RATE                                    #
    # ------------------------------------------------------------------ #

    def _compute_prior_exposure_rate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute the recent prior-antibiotic-exposure rate per
        (year_month, pathogen, drug_class, county) group.

        This is a real, per-record signal — the proportion of records in
        the group with documented prior antibiotic exposure — not a
        fabricated one. It is the closest honest proxy this dataset
        supports for antibiotic-use pressure; it is **not** the same
        thing as prescription/dispensing volume, which this dataset does
        not contain, and callers (e.g. the explainability layer) should
        not describe it as such.

        Records where exposure is genuinely unknown (``None`` — the
        source data's "Unknown"/"Not applicable" values) are excluded
        from both the numerator and denominator, rather than being
        counted as "no exposure" — treating an unknown as a negative
        would silently bias the rate downward.

        Args:
            df: Prepared DataFrame with a ``prior_antibiotic_exposure``
                column of True/False/None values.

        Returns:
            DataFrame with columns ``[year_month, pathogen_name,
            drug_class, county_code, prior_antibiotic_exposure_rate]``,
            or an empty DataFrame if the source column isn't present or
            every value is unknown.
        """
        if "prior_antibiotic_exposure" not in df.columns:
            logger.debug(
                "No prior_antibiotic_exposure column — skipping exposure rate"
            )
            return pd.DataFrame()

        working = df.dropna(subset=["prior_antibiotic_exposure"]).copy()
        if working.empty:
            logger.debug(
                "All prior_antibiotic_exposure values are unknown — skipping"
            )
            return pd.DataFrame()

        working["prior_antibiotic_exposure"] = (
            working["prior_antibiotic_exposure"].astype(bool).astype(int)
        )

        group_cols = ["year_month", "pathogen_name", "drug_class", "county_code"]
        try:
            rate = (
                working.groupby(group_cols, observed=True)[
                    "prior_antibiotic_exposure"
                ]
                .mean()
                .reset_index()
                .rename(
                    columns={
                        "prior_antibiotic_exposure": "prior_antibiotic_exposure_rate"
                    }
                )
            )
        except Exception:
            logger.exception("Failed to compute prior antibiotic exposure rate")
            return pd.DataFrame()

        return rate

    # ------------------------------------------------------------------ #
    # 7. GEOGRAPHIC CLUSTERING                                            #
    # ------------------------------------------------------------------ #

    def _compute_geographic_clustering(
        self, base: pd.DataFrame, group_cols: List[str]
    ) -> pd.DataFrame:
        """Compute neighbouring county mean resistance rate.

        For each county, averages the resistance rates of its geographic
        neighbours for the same ``(pathogen, drug_class, month)`` tuple.

        Args:
            base: Base resistance DataFrame.
            group_cols: Full grouping columns list.

        Returns:
            DataFrame with ``neighbor_resistance_mean`` and
            ``neighbor_county_count`` columns.
        """
        # Build lookup: (year_month, pathogen, drug_class, county) → rate
        try:
            rate_lookup = base.set_index(
                ["year_month", "pathogen_name", "drug_class", "county_code"]
            )["resistance_rate"].to_dict()
        except Exception:
            logger.exception("Failed to build rate lookup for geographic clustering")
            return pd.DataFrame()

        neighbor_rates: List[Dict[str, Any]] = []

        for _, row in base.iterrows():
            key_parts = (
                row["year_month"],
                row["pathogen_name"],
                row["drug_class"],
            )
            county = row["county_code"]
            neighbors = self.adjacency.get(county, [])

            if neighbors:
                rates = [
                    rate_lookup.get((*key_parts, n))
                    for n in neighbors
                ]
                valid_rates = [r for r in rates if r is not None]
                neighbor_mean = float(np.mean(valid_rates)) if valid_rates else 0.0
                neighbor_count = len(valid_rates)
            else:
                neighbor_mean = 0.0
                neighbor_count = 0

            neighbor_rates.append(
                {
                    "year_month": row["year_month"],
                    "pathogen_name": row["pathogen_name"],
                    "drug_class": row["drug_class"],
                    "county_code": county,
                    "neighbor_resistance_mean": neighbor_mean,
                    "neighbor_county_count": neighbor_count,
                }
            )

        return pd.DataFrame(neighbor_rates)

    # ------------------------------------------------------------------ #
    # 8. RATE OF CHANGE                                                   #
    # ------------------------------------------------------------------ #

    def _compute_rate_of_change(
        self, base: pd.DataFrame, group_cols: List[str]
    ) -> pd.DataFrame:
        """Compute month-over-month delta and percentage change in resistance rate.

        Args:
            base: Base resistance DataFrame.
            group_cols: Full grouping columns list.

        Returns:
            DataFrame with ``resistance_rate_delta_1m`` (absolute difference)
            and ``resistance_rate_pct_change_1m`` (relative change) columns.
        """
        entity_cols = ["pathogen_name", "drug_class", "county_code"]
        base_sorted = base.sort_values(group_cols)

        results: List[pd.DataFrame] = []
        for _, group in base_sorted.groupby(entity_cols, observed=True):
            g = group.copy()
            g["resistance_rate_delta_1m"] = g["resistance_rate"].diff()
            g["resistance_rate_pct_change_1m"] = g["resistance_rate"].pct_change()
            # Replace inf/-inf values that arise from 0 denominators
            g["resistance_rate_pct_change_1m"] = g[
                "resistance_rate_pct_change_1m"
            ].replace([np.inf, -np.inf], 0.0)
            results.append(
                g[
                    group_cols
                    + [
                        "resistance_rate_delta_1m",
                        "resistance_rate_pct_change_1m",
                    ]
                ]
            )

        if not results:
            return pd.DataFrame()

        return pd.concat(results, ignore_index=True)

    # ------------------------------------------------------------------ #
    # UTILITY — Get numeric feature columns for model input               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_feature_columns(df: pd.DataFrame) -> List[str]:
        """Return the list of numeric feature columns suitable for model input.

        Excludes identifier / categorical columns (``year_month``,
        ``pathogen_name``, ``drug_class``, ``county_code``, etc.) and
        string columns.

        Args:
            df: Feature DataFrame produced by the pipeline.

        Returns:
            Sorted list of numeric column names usable as model features.
        """
        exclude = {
            "year_month",
            "pathogen_name",
            "drug_class",
            "county_code",
            "county_name",
            "sub_county",
            "sector",
            "record_id",
            "drug_name",
            "aware_class",
            "atc_code",
            "sir",
            "sample_collection_date",
            "lab_report_date",
        }
        return sorted(
            col
            for col in df.select_dtypes(include=[np.number]).columns
            if col not in exclude
        )

    # ------------------------------------------------------------------ #
    # INTERNAL — metadata builder                                         #
    # ------------------------------------------------------------------ #

    def _build_metadata(
        self, features: pd.DataFrame, elapsed: float
    ) -> None:
        """Build and store FeatureMetadata from the computed features.

        Args:
            features: The computed feature DataFrame.
            elapsed: Wall-clock computation time in seconds.
        """
        if features.empty:
            self.metadata = FeatureMetadata(computation_time_seconds=elapsed)
            return

        # Determine date range from year_month periods
        try:
            periods = features["year_month"].dropna()
            if not periods.empty:
                min_period = periods.min()
                max_period = periods.max()
                date_range = (
                    min_period.start_time.date(),
                    max_period.end_time.date(),
                )
            else:
                date_range = (date.today(), date.today())
        except Exception:
            date_range = (date.today(), date.today())

        pathogens = (
            features["pathogen_name"].unique().tolist()
            if "pathogen_name" in features.columns
            else []
        )
        drug_classes = (
            features["drug_class"].unique().tolist()
            if "drug_class" in features.columns
            else []
        )
        counties = (
            features["county_code"].unique().tolist()
            if "county_code" in features.columns
            else []
        )

        self.metadata = FeatureMetadata(
            feature_count=len(self.get_feature_columns(features)),
            record_count=len(features),
            date_range=date_range,
            pathogens=pathogens,
            drug_classes=drug_classes,
            counties=counties,
            computation_time_seconds=round(elapsed, 4),
        )