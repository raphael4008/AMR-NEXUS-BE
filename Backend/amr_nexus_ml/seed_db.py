import click
import pandas as pd
from datetime import datetime
from src.database import SessionLocal
from src.db.models import AMRIsolateRecord
from src.utils.logger import logger


@click.command()
@click.option(
    "--file-path",
    default="data/AMR_Nexus_Kenya_Dataset_IMPROVED.csv",
    help="Path to the Excel or CSV dataset file.",
)
def seed_database(file_path: str) -> None:
    """
    Seeds the AMR-Nexus SQLite/PostgreSQL database with records from the Kenya surveillance dataset.
    """
    logger.info(f"Starting database population from: {file_path}")
    db = SessionLocal()

    try:
        # Automatically handle Excel spreadsheets disguised as CSV or standard Excel files
        if file_path.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_path)
        else:
            try:
                df = pd.read_csv(file_path, encoding="latin-1")
            except Exception:
                df = pd.read_excel(file_path)

        logger.info(f"Successfully loaded {len(df)} rows from dataset.")

        existing_count = db.query(AMRIsolateRecord).count()
        logger.info(f"Current records in database: {existing_count}")

        if existing_count > 0:
            logger.info("Database already contains records. Skipping seed.")
            return

        logger.info("Seeding database records in batches...")
        records_to_insert = []

        for _, row in df.iterrows():
            classification_val = str(row.get("classification", "Standard"))
            resistance_val = float(row.get("resistance_percent", 50.0) or 50.0)

            # Strict boolean evaluations for flags
            is_mdr = bool(
                "MDR" in classification_val.upper()
                or "XDR" in classification_val.upper()
                or resistance_val >= 70.0
            )
            is_anomaly = bool(resistance_val >= 75.0 or "XDR" in classification_val.upper())

            record = AMRIsolateRecord(
                sector=str(row.get("sector", "Environment")),
                pathogen_code=str(row.get("pathogen_code", "eco")),
                specimen_type=str(row.get("specimen_type", "Blood")),
                county=str(row.get("county", "Nairobi")),
                antibiotic_class=str(row.get("antibiotic_class", "Beta-lactam")),
                sample_month=str(row.get("sample_month", "2026-06")),
                sir_result=classification_val,
                mdr_flag=is_mdr,
                anomaly_flag=is_anomaly,
                anomaly_score=float(resistance_val / 100.0),
                mdr_probability=float(0.85 if is_mdr else 0.25),
                created_at=datetime.utcnow(),
            )
            records_to_insert.append(record)

            # Batch insert every 500 records to ensure high performance and low memory overhead
            if len(records_to_insert) >= 500:
                db.bulk_save_objects(records_to_insert)
                db.commit()
                records_to_insert = []

        # Commit any remaining records
        if records_to_insert:
            db.bulk_save_objects(records_to_insert)
            db.commit()

        logger.info("Database successfully populated with all surveillance records!")

    except Exception as e:
        db.rollback()
        logger.error(f"Seeding failed: {str(e)}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()