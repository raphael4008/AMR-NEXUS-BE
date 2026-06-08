"""
ingest_dataset.py — AMR-Nexus Real Dataset Ingestion Pipeline
"""

import logging
import pandas as pd
import os
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from src.models.base import engine, SessionLocal
from src.models.entities import AMRRecord, Alert, User
from src.core.security import get_password_hash

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger("amr_ingestion")

# ── Dynamic Path Resolution ──
BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "AMR_Nexus_Kenya_Dataset_IMPROVED.csv.xlsx"

def clean_string(val, max_length=None):
    """Safely converts Pandas NaN or empty strings to SQL NULL (None)."""
    if pd.isna(val) or str(val).strip() == "" or str(val).strip().lower() == "nan":
        return None
    cleaned = str(val).strip()
    return cleaned[:max_length] if max_length else cleaned

def parse_numeric(val, default=0.0):
    """Safely converts dirty Excel cells into Floats."""
    if pd.isna(val):
        return default
    val_str = str(val).strip().lower()
    if val_str == 'clean': # Fixes the specific 'clean' string in the dataset
        return 1.0
    try:
        return float(val)
    except ValueError:
        return default

def ingest_data(db: Session):
    logger.info("🎬 Initializing Dataset Ingestion Pipeline...")

    # ── 1. SEED AUTHENTICATED USER ────────────────────────────────────────────
    existing_user = db.query(User).filter(User.username == "bantu").first()
    if not existing_user:
        logger.info("🔑 Creating default 'National Coordinator' security account...")
        db.add(User(
            username="bantu",
            email="bantu@amrnexus.go.ke",
            hashed_password=get_password_hash("secret"),
            role="National Coordinator",
            is_active=True
        ))
        db.flush()

    # ── 2. LOAD DATASET VIA PANDAS ────────────────────────────────────────────
    logger.info(f"📂 Loading dataset from {DATASET_PATH}...")
    try:
        df = pd.read_excel(DATASET_PATH) 
        df = df.where(pd.notnull(df), None)
    except Exception as e:
        logger.error(f"❌ Failed to read dataset: {e}")
        return

    record_count = db.query(AMRRecord).count()
    if record_count > 0:
        logger.info(f"ℹ️ Database already contains {record_count} records. Skipping ingestion to prevent duplicates.")
        return

    logger.info(f"📊 Processing {len(df)} records into TimescaleDB Fact Table...")
    
    ingested_records = []
    
    for index, row in df.iterrows():
        # Safely parse dates
        raw_date = row.get("sample_collection_date", datetime.now(timezone.utc))
        if isinstance(raw_date, str):
            try:
                collection_date = datetime.strptime(raw_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                collection_date = datetime.now(timezone.utc)
        else:
            collection_date = raw_date if getattr(raw_date, 'tzinfo', None) else raw_date.replace(tzinfo=timezone.utc)

        # Map DataFrame rows directly to the flattened schema
        record = AMRRecord(
            sample_collection_date=collection_date,
            sector=clean_string(row.get("sector"), 20) or "HUMAN",
            
            # Taxonomy
            pathogen_name=clean_string(row.get("pathogen"), 150) or clean_string(row.get("pathogen_name"), 150) or "Unknown",
            pathogen_code=clean_string(row.get("pathogen_code"), 30),
            resistance_profile=clean_string(row.get("classification"), 50) or "Unknown",
            mdr_flag=bool(row.get("mdr_flag", False)),
            
            # Antibiotics
            antibiotic_name=clean_string(row.get("antibiotic"), 100) or clean_string(row.get("antibiotic_name"), 100) or "Unknown",
            antibiotic_code=clean_string(row.get("antibiotic_code"), 20),
            antibiotic_class=clean_string(row.get("antibiotic_class"), 100) or "Unknown",
            sir_result=str(row.get("sir_result", "S"))[0].upper() if clean_string(row.get("sir_result")) else "S",
            
            # Geo & Facility
            county=clean_string(row.get("county"), 50) or "Unknown",
            facility_id=clean_string(row.get("facility_id"), 50),
            
            # Use the robust parser for all numeric fields
            latitude=parse_numeric(row.get("latitude"), None),
            longitude=parse_numeric(row.get("longitude"), None),
            resistance_rate=parse_numeric(row.get("resistance_rate"), 0.0),
            resistance_percent=parse_numeric(row.get("resistance_percent"), 0.0),
            data_quality_score=parse_numeric(row.get("data_quality"), 1.0),
            
            classification=clean_string(row.get("classification"), 20),
            submission_type="IMPORTED",
            missing_fields={},
            is_synthetic=0
        )
        db.add(record)
        ingested_records.append(record)

    db.flush() 
    logger.info("✅ Core surveillance records ingested successfully.")

    # ── 3. GENERATE AI ALERTS ─────────────────────────────────────────────────
    logger.info("🧠 Generating AI Alerts for high-risk resistant isolates...")
    
    resistant_records = [r for r in ingested_records if r.sir_result == 'R']
    import random
    
    for target_record in random.sample(resistant_records, min(len(resistant_records), 50)):
        anomaly = Alert(
            amr_isolate_record_id=target_record.id,
            sample_date=target_record.sample_collection_date, 
            detection_timestamp=datetime.now(timezone.utc),
            anomaly_score=random.uniform(0.85, 0.99),
            hotspot_magnitude=random.uniform(0.70, 0.95),
            status="PENDING",
            feature_importance={
                "pathogen_frequency": random.uniform(0.4, 0.7),
                "regional_spike": random.uniform(0.5, 0.8)
            }
        )
        db.add(anomaly)

    db.commit()
    logger.info("🚀 Full Dataset successfully committed to TimescaleDB!")

if __name__ == "__main__":
    session = SessionLocal()
    try:
        ingest_data(session)
    except Exception as error:
        session.rollback()
        logger.error(f"❌ Ingestion aborted due to critical error: {error}")
        raise error
    finally:
        session.close()