from typing import Optional
from pydantic import BaseModel, Field


class AMRRecordIn(BaseModel):
    sector: str = Field(..., max_length=20)
    sub_sector: str = Field(..., max_length=50)
    pathogen_code: str = Field(..., max_length=20)
    specimen_type: str = Field(..., max_length=100)
    animal_species: Optional[str] = Field(default=None, max_length=100)
    production_system: Optional[str] = Field(default=None, max_length=50)
    county: str = Field(..., max_length=100)
    urban_rural: Optional[str] = Field(default=None, max_length=10)
    patient_age_years: Optional[float] = Field(default=None, ge=0, le=120)
    patient_sex: Optional[str] = Field(default=None, max_length=1)
    ward_type: Optional[str] = Field(default=None, max_length=50)
    prior_antibiotic_exposure: Optional[bool] = None
    infection_origin: Optional[str] = Field(default=None, max_length=20)
    antibiotic_class: str = Field(..., max_length=100)
    test_method: str = Field(..., max_length=50)
    sample_month: int = Field(..., ge=1, le=12)
    phone_number: Optional[str] = Field(default=None, max_length=20)


class PredictionResponse(BaseModel):
    mdr_flag: bool
    mdr_probability: float
    anomaly_detected: bool
    anomaly_score: float
    shap_top_feature: str
    shap_value: float
    shap_summary: str


class EmailReportRequest(BaseModel):
    email: str
    format: str = Field(default="pdf", max_length=10)


class CommentCreate(BaseModel):
    text: str = Field(..., max_length=1000)
    user_name: str = Field(default="Anonymous", max_length=100)


class GuidanceRequest(BaseModel):
    pathogen_code: str = Field(..., max_length=20)
    resistance_pattern: str = Field(..., max_length=200)
    user_role: str = Field(..., max_length=50)
    county: Optional[str] = Field(default=None, max_length=100)
