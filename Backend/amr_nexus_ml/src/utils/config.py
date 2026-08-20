import json
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    DATA_FILE_PATH: str = os.environ["DATA_FILE_PATH"]
    DB_URL: str = os.environ["DATABASE_URL"]
    MODEL_DIR: Path = Path(os.environ["MODEL_DIR"])
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ANOMALY_CONTAMINATION: float = float(os.environ["ANOMALY_CONTAMINATION"])
    
    XGB_PARAMS: dict = {
        "n_estimators": int(os.getenv("XGB_N_ESTIMATORS", "200")),
        "max_depth": int(os.getenv("XGB_MAX_DEPTH", "6")),
        "learning_rate": float(os.getenv("XGB_LEARNING_RATE", "0.05")),
        "tree_method": os.getenv("XGB_TREE_METHOD", "hist"),
        "random_state": int(os.getenv("XGB_RANDOM_STATE", "42")),
    }

    MDR_CLASSES: list = json.loads(os.getenv("MDR_CLASSES", '["MDR", "XDR", "PDR"]'))
    RESISTANCE_THRESHOLD: float = float(os.getenv("RESISTANCE_THRESHOLD", "0.5"))
    GEOGRAPHY_COLUMN: str = os.getenv("GEOGRAPHY_COLUMN", "county")
    CRITICAL_COLUMNS: list = json.loads(
        os.getenv(
            "CRITICAL_COLUMNS", 
            '["mdr_flag", "pathogen_code", "sir_result", "antibiotic_class", "sector", "county", "sample_month"]'
        )
    )
    
    DEFAULT_SAMPLE_MONTH: int = int(os.getenv("DEFAULT_SAMPLE_MONTH", "1"))
    DEFAULT_AGE_FALLBACK: float = float(os.getenv("DEFAULT_AGE_FALLBACK", "-1.0"))
    DEFAULT_STRING_FALLBACK: str = os.getenv("DEFAULT_STRING_FALLBACK", "unknown")
    DEFAULT_TEST_METHOD: str = os.getenv("DEFAULT_TEST_METHOD", "Disk diffusion")

    PATHOGEN_MAP: dict = {
        "escherichia coli": "eco",
        "klebsiella pneumoniae": "kpn",
        "staphylococcus aureus": "sau",
        "salmonella spp.": "sal",
        "campylobacter jejuni": "cam",
        "pseudomonas aeruginosa": "pae",
        "acinetobacter baumannii": "aba",
        "enterococcus faecalis": "efc",
        "streptococcus pneumoniae": "spn",
        "enterobacter cloacae": "ecl"
    }
    ANTIBIOTIC_MAP: dict = {
        "ciprofloxacin": "Fluoroquinolone",
        "amoxicillin": "Penicillin",
        "gentamicin": "Aminoglycoside",
        "carbapenem": "Carbapenem",
        "tetracycline": "Tetracycline",
        "azithromycin": "Macrolide",
        "ceftriaxone": "Cephalosporin",
        "trimethoprim": "Folate inhibitor",
        "vancomycin": "Glycopeptide",
        "colistin": "Polymyxin"
    }
    SECTOR_REPLACEMENTS: dict = {"POULTRY": "ANIMAL"}
    SUB_SECTOR_MAP: dict = {"HUMAN": "Inpatient", "ANIMAL": "Poultry-Broiler"}


config = Config()
