"""
utils/synthetic_gen.py — High-Fidelity Kenyan AMR Synthetic Data Generator

Generates statistically realistic isolate records spanning ≥7 Kenyan counties,
Human + Animal (poultry-focus) + Environment sectors, and 6 priority pathogens.

Deliberately injects:
  - ~15% non-critical missing fields (sub_county, facility_type) to exercise the DataCleaner
  - ~5% critical failures (missing pathogen_name or county) to validate rejection logic

Usage:
  # CLI
  python -m src.utils.synthetic_gen --count 600

  # Programmatic
  from src.utils.synthetic_gen import SyntheticDataGenerator
  gen = SyntheticDataGenerator(seed=42)
  records = gen.generate(n=600)
"""

import argparse
import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Kenyan AMR Domain Constants ───────────────────────────────────────────────────

COUNTIES = [
    "Nairobi", "Kiambu", "Mombasa", "Kisumu",
    "Nakuru", "Eldoret", "Machakos",
]

SUB_COUNTIES: Dict[str, List[str]] = {
    "Nairobi":  ["Westlands", "Dagoretti", "Embakasi East", "Langata", "Kasarani"],
    "Kiambu":   ["Thika Town", "Githunguri", "Ruiru", "Limuru", "Kikuyu"],
    "Mombasa":  ["Mvita", "Nyali", "Likoni", "Changamwe", "Jomvu"],
    "Kisumu":   ["Kisumu East", "Kisumu West", "Nyando", "Muhoroni", "Seme"],
    "Nakuru":   ["Nakuru Town East", "Nakuru Town West", "Subukia", "Rongai", "Molo"],
    "Eldoret":  ["Turbo", "Ainabkoi", "Moiben", "Soy", "Kesses"],
    "Machakos": ["Machakos Town", "Mavoko", "Masinga", "Yatta", "Matungulu"],
}

# Sector distribution: 50% human, 35% animal (poultry), 15% environment
SECTORS_WEIGHTED = (
    ["human"] * 50 + ["animal"] * 35 + ["environment"] * 15
)

# Human sector facilities
HUMAN_FACILITIES = [
    "Tertiary Hospital", "County Referral Hospital", "Sub-County Hospital",
    "Health Centre", "Dispensary", "Private Clinic", "Mission Hospital",
]

# Animal/Poultry sector facilities
ANIMAL_FACILITIES = [
    "Poultry Farm (Commercial)", "Poultry Farm (Smallholder)", "Veterinary Clinic",
    "Agro-vet Shop", "Livestock Market", "Slaughterhouse",
]

# Environment sector facilities
ENVIRONMENT_FACILITIES = [
    "River Water Sampling Site", "Wastewater Treatment Plant",
    "Irrigation Canal", "Borehole Site", "Market Effluent Point",
]

# WHO GLASS priority pathogens with sector affinity
PATHOGENS: Dict[str, List[str]] = {
    "human":       ["E. coli", "K. pneumoniae", "S. aureus", "Streptococcus pneumoniae", "Acinetobacter baumannii"],
    "animal":      ["Salmonella spp.", "Campylobacter spp.", "E. coli", "S. aureus", "Enterococcus spp."],
    "environment": ["E. coli", "Salmonella spp.", "Pseudomonas aeruginosa", "K. pneumoniae", "Acinetobacter baumannii"],
}

# WHO AWaRe classified antimicrobials
ANTIMICROBIALS: Dict[str, Dict[str, str]] = {
    "Ciprofloxacin":  {"aware_tier": "Watch",  "class": "Fluoroquinolone"},
    "Amoxicillin":    {"aware_tier": "Access", "class": "Penicillin"},
    "Ceftriaxone":    {"aware_tier": "Watch",  "class": "3rd-gen Cephalosporin"},
    "Tetracycline":   {"aware_tier": "Access", "class": "Tetracycline"},
    "Meropenem":      {"aware_tier": "Reserve","class": "Carbapenem"},
    "Colistin":       {"aware_tier": "Reserve","class": "Polymyxin"},
    "Amoxicillin-Clavulanate": {"aware_tier": "Access", "class": "Beta-lactam combo"},
    "Trimethoprim-Sulfamethoxazole": {"aware_tier": "Access", "class": "Sulfonamide"},
    "Chloramphenicol": {"aware_tier": "Watch", "class": "Amphenicol"},
    "Gentamicin":     {"aware_tier": "Access", "class": "Aminoglycoside"},
}

# SIR distribution: 60% Sensitive, 30% Resistant, 10% Intermediate (GLASS-aligned)
SIR_CHOICES_WEIGHTED = ["Sensitive"] * 60 + ["Resistant"] * 30 + ["Intermediate"] * 10


class SyntheticDataGenerator:
    """
    Generates statistically realistic Kenyan AMR One Health isolate records
    for seeding the AMR-Nexus development and validation database.
    """

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self._start_date = datetime(2023, 1, 1)
        self._end_date = datetime(2026, 5, 1)

    def _random_timestamp(self) -> datetime:
        delta = self._end_date - self._start_date
        random_days = random.randint(0, delta.days)
        return self._start_date + timedelta(days=random_days, hours=random.randint(0, 23))

    def _make_record(self, inject_non_critical_gap: bool, inject_critical_failure: bool) -> Dict[str, Any]:
        sector = random.choice(SECTORS_WEIGHTED)
        county = random.choice(COUNTIES)
        sub_counties = SUB_COUNTIES[county]

        pathogen = random.choice(PATHOGENS[sector])
        drug = random.choice(list(ANTIMICROBIALS.keys()))
        result = random.choice(SIR_CHOICES_WEIGHTED)

        # Facility based on sector
        if sector == "human":
            facility = random.choice(HUMAN_FACILITIES)
        elif sector == "animal":
            facility = random.choice(ANIMAL_FACILITIES)
        else:
            facility = random.choice(ENVIRONMENT_FACILITIES)

        sub_county = random.choice(sub_counties)
        mic_value = round(random.uniform(0.001, 128.0), 3) if random.random() > 0.3 else None

        record: Dict[str, Any] = {
            "sector": sector,
            "pathogen_name": pathogen,
            "antimicrobial_agent": drug,
            "county": county,
            "sub_county": sub_county,
            "facility_type": facility,
            "result_value": result,
            "mic_value": mic_value,
            "is_synthetic": 1,
            "hl7_fhir_id": f"FHIR-KE-{random.randint(100000, 999999)}",
            "woah_reference": f"WOAH-{county[:3].upper()}-{random.randint(1000, 9999)}",
            "timestamp": self._random_timestamp().isoformat(),
        }

        # ── Inject non-critical gaps (~15% of records) ────────────────────────
        if inject_non_critical_gap:
            gap_type = random.choice(["sub_county", "facility_type", "both"])
            if gap_type in ("sub_county", "both"):
                record["sub_county"] = None
            if gap_type in ("facility_type", "both"):
                record["facility_type"] = None

        # ── Inject critical failures (~5% of records) ─────────────────────────
        if inject_critical_failure:
            critical_field = random.choice(["pathogen_name", "county"])
            record[critical_field] = None

        return record

    def generate(self, n: int = 600) -> List[Dict[str, Any]]:
        """
        Generates n synthetic isolate records with realistic distributions.

        Args:
            n: Number of records to generate (≥500 for July 14 spec).

        Returns:
            List of raw record dicts (pre-DataCleaner) with deliberate data quality variations.
        """
        records = []
        critical_failure_count = max(1, int(n * 0.05))   # ~5% critical failures
        non_critical_gap_count = max(1, int(n * 0.15))   # ~15% non-critical gaps

        critical_indices = set(random.sample(range(n), critical_failure_count))
        gap_indices = set(random.sample(
            [i for i in range(n) if i not in critical_indices],
            min(non_critical_gap_count, n - len(critical_indices))
        ))

        for i in range(n):
            record = self._make_record(
                inject_non_critical_gap=(i in gap_indices),
                inject_critical_failure=(i in critical_indices),
            )
            records.append(record)

        logger.info(
            "Generated %d synthetic records: ~%d critical failures, ~%d non-critical gaps.",
            n, len(critical_indices), len(gap_indices)
        )
        return records

    def seed_database(self, db, n: int = 600) -> Dict[str, int]:
        """
        Pipes generated records through DataCleaner and bulk-inserts
        clean records into the database.

        Args:
            db: Active SQLAlchemy session.
            n: Number of records to generate and attempt insertion.

        Returns:
            Dict with {"generated", "persisted", "rejected"} counts.
        """
        from src.services.ingestion.cleaner import DataCleaner
        from src.models.entities import AMRRecord, SectorEnum

        cleaner = DataCleaner(threshold=0.4)
        raw_records = self.generate(n=n)
        clean_df, failed = cleaner.process_dirty_data(raw_records)

        persisted = 0
        for _, row in clean_df.iterrows():
            sector_raw = str(row.get("sector", "human")).lower().split(".")[-1]
            try:
                sector_enum = SectorEnum(sector_raw)
            except ValueError:
                sector_enum = SectorEnum.HUMAN

            # Parse timestamp if present
            ts = None
            if row.get("timestamp"):
                try:
                    ts = datetime.fromisoformat(str(row["timestamp"]))
                except (ValueError, TypeError):
                    ts = None

            record = AMRRecord(
                sector=sector_enum,
                pathogen_name=str(row.get("pathogen_name", "")),
                antimicrobial_agent=str(row.get("antimicrobial_agent", "")),
                county=str(row.get("county", "")),
                sub_county=row.get("sub_county") or None,
                facility_type=row.get("facility_type") or None,
                result_value=str(row.get("result_value", "")),
                mic_value=float(row["mic_value"]) if row.get("mic_value") else None,
                is_synthetic=1,
                data_quality_score=float(row.get("data_quality_score", 1.0)),
                missing_fields=row.get("missing_fields") if isinstance(row.get("missing_fields"), list) else None,
                hl7_fhir_id=row.get("hl7_fhir_id") or None,
                woah_reference=row.get("woah_reference") or None,
                timestamp=ts or datetime.now(timezone.utc),
            )
            db.add(record)
            persisted += 1

        db.commit()
        result = {"generated": n, "persisted": persisted, "rejected": len(failed)}
        logger.info("Seeding complete: %s", result)
        return result


# ── CLI Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import os

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(
        description="AMR-Nexus Synthetic Data Generator — seeds the PostgreSQL database."
    )
    parser.add_argument(
        "--count", type=int, default=600, help="Number of records to generate (default: 600)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Generate records without writing to DB (prints stats only)"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)"
    )
    args = parser.parse_args()

    gen = SyntheticDataGenerator(seed=args.seed)

    if args.dry_run:
        records = gen.generate(n=args.count)
        county_dist = {}
        sector_dist = {}
        sir_dist = {}
        for r in records:
            county_dist[r.get("county", "NONE")] = county_dist.get(r.get("county", "NONE"), 0) + 1
            sector_dist[r.get("sector", "NONE")] = sector_dist.get(r.get("sector", "NONE"), 0) + 1
            sir_dist[r.get("result_value", "NONE")] = sir_dist.get(r.get("result_value", "NONE"), 0) + 1

        print(f"\n✅ DRY RUN: Generated {len(records)} records")
        print(f"\nCounty distribution:  {county_dist}")
        print(f"Sector distribution:  {sector_dist}")
        print(f"SIR distribution:     {sir_dist}")
        critical = sum(1 for r in records if not r.get("pathogen_name") or not r.get("county"))
        print(f"Critical failures:    {critical} ({critical/len(records)*100:.1f}%)")
        sys.exit(0)

    # Real seeding — requires DB connection
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
    from src.models.base import SessionLocal, engine, Base
    from src.models.entities import AMRRecord  # noqa — ensures tables are created

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        result = gen.seed_database(db=db, n=args.count)
        print(
            f"\n✅ Seeding complete:\n"
            f"   Generated: {result['generated']}\n"
            f"   Persisted: {result['persisted']}\n"
            f"   Rejected:  {result['rejected']}\n"
        )
    finally:
        db.close()
