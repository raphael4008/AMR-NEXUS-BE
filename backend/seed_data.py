"""
seed_data.py — AMR-Nexus Realistic Kenya AMR Data Seeder
=========================================================
Run from project root:
    cd /home/bantu/Documents/amr-nexus-backend/backend
    python seed_data.py

Inserts:
  - 600 AMRRecord isolates spanning 12 months (Jan–Dec 2025)
  - 80  Alert rows (anomaly flags on high-risk records)
  
Uses asyncpg directly — no ARQ worker needed.
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# ── Import your models ────────────────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from src.models.entities import AMRRecord, Alert
from src.core.config import settings

# ── Kenya realistic data tables ───────────────────────────────────────────────

COUNTIES = [
    "Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret",
    "Meru", "Nyeri", "Kakamega", "Garissa", "Kilifi",
    "Kitui", "Machakos", "Bungoma", "Homa Bay", "Migori",
]

PATHOGENS = [
    ("Klebsiella pneumoniae",  "KLPN"),
    ("Escherichia coli",       "ECOL"),
    ("Staphylococcus aureus",  "SAUR"),
    ("Acinetobacter baumannii","ACBA"),
    ("Pseudomonas aeruginosa", "PSAE"),
    ("Salmonella typhi",       "SALT"),
    ("Streptococcus pneumoniae","STPN"),
    ("Enterococcus faecalis",  "ENFA"),
    ("Mycobacterium tuberculosis","MYTB"),
    ("Candida auris",          "CAUD"),
]

ANTIBIOTICS = [
    ("Ciprofloxacin",    "CIP",  "Fluoroquinolone"),
    ("Ampicillin",       "AMP",  "Penicillin"),
    ("Meropenem",        "MEM",  "Carbapenem"),
    ("Tetracycline",     "TET",  "Tetracycline"),
    ("Ceftriaxone",      "CRO",  "Cephalosporin"),
    ("Azithromycin",     "AZM",  "Macrolide"),
    ("Gentamicin",       "GEN",  "Aminoglycoside"),
    ("Trimethoprim",     "TMP",  "Sulphonamide"),
    ("Vancomycin",       "VAN",  "Glycopeptide"),
    ("Colistin",         "COL",  "Polymyxin"),
]

SECTORS = ["HUMAN", "ANIMAL", "ENVIRONMENT"]

SPECIMEN_TYPES = [
    "Blood", "Urine", "Sputum", "Wound Swab",
    "Stool", "CSF", "Pus Swab", "Throat Swab",
]

FACILITY_TYPES = [
    "County Referral Hospital", "Health Centre", "District Hospital",
    "Private Hospital", "Dispensary",
]


def rand_date_in_month(year: int, month: int) -> datetime:
    """Random UTC datetime within a given year-month."""
    first = datetime(year, month, 1, tzinfo=timezone.utc)
    days_in_month = 28 if month == 2 else (30 if month in [4,6,9,11] else 31)
    offset = timedelta(days=random.randint(0, days_in_month - 1),
                       hours=random.randint(0, 23),
                       minutes=random.randint(0, 59))
    return first + offset


def make_record(year: int, month: int, idx: int) -> dict:
    county      = random.choice(COUNTIES)
    pathogen    = random.choice(PATHOGENS)
    antibiotic  = random.choice(ANTIBIOTICS)
    sector      = random.choices(SECTORS, weights=[65, 25, 10])[0]

    # Resistance probability varies by pathogen to create realistic gradients
    pathogen_resistance = {
        "Klebsiella pneumoniae":   0.62,
        "Escherichia coli":        0.55,
        "Staphylococcus aureus":   0.48,
        "Acinetobacter baumannii": 0.75,
        "Pseudomonas aeruginosa":  0.58,
        "Salmonella typhi":        0.40,
        "Streptococcus pneumoniae":0.35,
        "Enterococcus faecalis":   0.30,
        "Mycobacterium tuberculosis": 0.20,
        "Candida auris":           0.70,
    }
    # Counties with higher resistance (simulate hotspots)
    county_modifier = {
        "Nairobi": 0.10, "Mombasa": 0.08, "Kisumu": 0.05,
        "Garissa": 0.12, "Kilifi": 0.07,
    }
    base_r = pathogen_resistance.get(pathogen[0], 0.5)
    mod    = county_modifier.get(county, 0.0)
    resist = random.random() < min(base_r + mod, 0.95)

    sir_result        = "R" if resist else ("I" if random.random() < 0.1 else "S")
    anomaly_score     = round(random.uniform(0.7, 0.99), 4) if resist and random.random() < 0.25 else round(random.uniform(0.01, 0.55), 4)
    anomaly_flag      = anomaly_score > 0.65
    resistance_pct    = round(random.uniform(60, 95), 2) if resist else round(random.uniform(5, 35), 2)
    sample_date       = rand_date_in_month(year, month)
    rec_id            = uuid.uuid4()

    return {
        "id":                   rec_id,
        "sample_collection_date": sample_date,
        "sample_year":          year,
        "sample_month":         month,
        "sample_week":          sample_date.isocalendar()[1],
        "sector":               sector,
        "pathogen_name":        pathogen[0],
        "pathogen_code":        None,   # no FK enforcement in seed
        "antibiotic_name":      antibiotic[0],
        "antibiotic_code":      None,
        "antibiotic_class":     antibiotic[2],
        "sir_result":           sir_result,
        "county":               county,
        "sub_county":           f"{county} Central",
        "region":               county,
        "country_code":         "KEN",
        "country_name":         "Kenya",
        "facility_type":        random.choice(FACILITY_TYPES),
        "facility_id":          None,
        "specimen_type":        random.choice(SPECIMEN_TYPES),
        "sample_source":        "Clinical",
        "resistance_rate":      round(resistance_pct / 100, 4),
        "resistance_percent":   resistance_pct,
        "resistance_profile":   "MDR" if resist else "Non-MDR",
        "mdr_flag":             resist,
        "anomaly_score":        anomaly_score,
        "anomaly_flag":         anomaly_flag,
        "alert_triggered":      anomaly_flag,
        "data_quality_score":   round(random.uniform(0.78, 1.0), 3),
        "is_synthetic":         1,
        "submission_type":      "SYNTHETIC",
        "latitude":             None,
        "longitude":            None,
        "shap_top_feature":     "resistance_rate" if anomaly_flag else None,
        "shap_value":           round(random.uniform(0.3, 0.8), 4) if anomaly_flag else None,
        "model_version":        "1.3.0",
        "created_at":           datetime.now(timezone.utc),
        "updated_at":           datetime.now(timezone.utc),
        "deleted_at":           None,
        "infarm_compliant":     False,
        "animuse_compliant":    False,
        "glass_eligible":       False,
    }


async def seed():
    engine = create_async_engine(settings.DATABASE_URI, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # ── Check current counts ──────────────────────────────────────────────
        count_res = await session.execute(text("SELECT COUNT(*) FROM amr_isolate_records"))
        existing  = count_res.scalar_one()
        if existing >= 200:
            print(f"✅ Database already has {existing} records — skipping seed.")
            return

        print(f"🌱 Seeding AMR-Nexus with realistic Kenya data…")

        # ── Build 600 records spread across Jan–Dec 2025 ─────────────────────
        records = []
        for month in range(1, 13):
            per_month = random.randint(45, 55)   # ~600 total
            for idx in range(per_month):
                records.append(make_record(2025, month, idx))

        # Add some 2024 data for longer trend view (3 months)
        for month in [10, 11, 12]:
            for idx in range(random.randint(20, 30)):
                records.append(make_record(2024, month, idx))

        random.shuffle(records)
        print(f"   Inserting {len(records)} AMR records…")

        # Batch insert in chunks of 100
        for i in range(0, len(records), 100):
            chunk = records[i:i+100]
            session.add_all([AMRRecord(**r) for r in chunk])
        await session.commit()
        print(f"   ✅ {len(records)} AMR records inserted")

        # ── Re-fetch the inserted records to create Alerts ────────────────────
        from sqlalchemy import select
        result    = await session.execute(
            select(AMRRecord.id, AMRRecord.sample_collection_date, AMRRecord.anomaly_score, AMRRecord.anomaly_flag)
            .where(AMRRecord.anomaly_flag == True)    # noqa: E712
            .limit(120)
        )
        flagged = result.all()

        print(f"   Inserting {len(flagged)} Alert rows for anomalous records…")
        alerts = []
        for row in flagged:
            a_score = float(row.anomaly_score or 0.75)
            alerts.append(Alert(
                id=uuid.uuid4(),
                amr_isolate_record_id=row.id,
                sample_date=row.sample_collection_date,
                anomaly_score=a_score,
                hotspot_magnitude=round(a_score * random.uniform(0.8, 1.2), 4),
                feature_importance={"resistance_rate": 0.45, "county": 0.25, "pathogen": 0.30},
                status=random.choices(["PENDING", "ACKNOWLEDGED"], weights=[75, 25])[0],
                detection_timestamp=datetime.now(timezone.utc) - timedelta(
                    hours=random.randint(0, 72)
                ),
            ))

        for i in range(0, len(alerts), 50):
            session.add_all(alerts[i:i+50])
        await session.commit()
        print(f"   ✅ {len(alerts)} Alerts inserted")

        # ── Final counts ──────────────────────────────────────────────────────
        r_cnt = (await session.execute(text("SELECT COUNT(*) FROM amr_isolate_records"))).scalar_one()
        a_cnt = (await session.execute(text("SELECT COUNT(*) FROM alerts"))).scalar_one()
        print(f"\n🎉 Seed complete!")
        print(f"   amr_isolate_records : {r_cnt}")
        print(f"   alerts              : {a_cnt}")
        print(f"\nRefresh the dashboard — charts should now show data.")


if __name__ == "__main__":
    asyncio.run(seed())
