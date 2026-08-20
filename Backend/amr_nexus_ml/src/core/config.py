from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "AMR-Nexus ML API"
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    DATABASE_URL: str

    MODEL_DIR: str = "./models"
    DATA_FILE_PATH: str = "./data/AMR_Nexus_Kenya_Dataset_IMPROVED.csv"

    
    FRONTEND_FEATURES: List[str] = [
        'sector', 'sub_sector', 'pathogen_code', 'specimen_type',
        'county', 'antibiotic_class', 'test_method', 'sample_month',
        'prior_antibiotic_exposure'
    ]

    SHAP_TOP_FEATURES: int = 3

    ALERT_MDR_THRESHOLD: float = 30.0
    ALERT_ANOMALY_DAYS: int = 7

    RISK_WEIGHTS: dict = {"anomaly": 0.4, "mdr": 0.4, "sample": 0.2}

    AT_USERNAME: str = "sandbox"
    AT_API_KEY: str = ""
    AT_SENDER_ID: str = "AMRNexus"
    ENABLE_SMS: bool = False

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = "reports@amrnexus.org"

    CLAUDE_API_KEY: str = ""

    DEFAULT_USER_NAME: str = "John Doe"
    DEFAULT_USER_EMAIL: str = "john.doe@amrnexus.org"
    DEFAULT_USER_ROLE: str = "epidemiologist"
    DEFAULT_USER_COUNTY: str = "Nairobi"

    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()