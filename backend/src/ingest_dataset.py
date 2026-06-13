import logging
import pandas as pd
from src.models.base import SessionLocal
from src.models.entities import AMRRecord, Alert, User
from src.services.ingestion.cleaner import DataCleaner
from src.core.security import get_password_hash
import random
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger("amr_ingestion")

def ingest_data(db):
    logger.info("🎬 Initializing Unified Ingestion Pipeline...")

    # 1. SEED USER
    existing_user = db.query(User).filter(User.username == "bantu").first()
    if not existing_user:
        db.add(User(
            username="bantu", email="bantu@amrnexus.go.ke",
            hashed_password=get_password_hash("secret"),
            role="National Coordinator", is_active=True
        ))
        db.flush()

    # 2. LOAD DATA
    df = pd.read_excel("AMR_Nexus_Kenya_Dataset_IMPROVED.csv.xlsx")
    raw_records = df.to_dict(orient="records")

    # 3. PROCESS VIA DATA CLEANER (Unchanged logic)
    cleaner = DataCleaner()
    clean_payload, failed_payload = cleaner.process_dirty_data(raw_records)
    
    logger.info(f"✅ Validation complete: {len(clean_payload)} clean, {len(failed_payload)} rejected.")

    # 4. INSERT INTO DB
    # Now we iterate through the cleaned list returned by your DataCleaner
    for rec in clean_payload:
        record = AMRRecord(**rec)
        db.add(record)
    
    db.commit()
    logger.info("🚀 Full Dataset successfully committed to TimescaleDB!")

if __name__ == "__main__":
    session = SessionLocal()
    try:
        ingest_data(session)
    except Exception as error:
        session.rollback()
        logger.error(f"❌ Ingestion aborted: {error}")
    finally:
        session.close()