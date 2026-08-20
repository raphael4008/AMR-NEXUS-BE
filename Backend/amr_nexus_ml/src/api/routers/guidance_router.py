import numpy as np
import pandas as pd
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from src.api.schemas import GuidanceRequest
from src.core.ml import get_model, get_preprocessor

guidance_router = APIRouter()

POTENTIAL_ALTERNATIVES: List[str] = [
    "Ceftriaxone",
    "Ceftazidime-avibactam",
    "Cefoxitin",
    "Amoxicillin",
    "Gentamicin",
    "Colistin"
]


@guidance_router.post(
    "/recommend",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str, Any]
)
async def get_clinical_guidance_recommendation(payload: GuidanceRequest) -> Dict[str, Any]:
    try:
        preprocessor = get_preprocessor()
        model = get_model()

        simulated_records = []
        for agent in POTENTIAL_ALTERNATIVES:
            simulated_records.append({
                "sector": "HUMAN",
                "sub_sector": "Inpatient",
                "pathogen_code": str(payload.pathogen_code).lower().strip(),
                "specimen_type": "unknown",
                "county": str(payload.county) if payload.county else "unknown",
                "antibiotic_class": agent,
                "test_method": "Disk diffusion",
                "sample_month": 1,
                "patient_age_years": 30.0,
                "patient_sex": "M",
                "ward_type": "General",
                "prior_antibiotic_exposure": False,
                "infection_origin": "Community",
                "animal_species": None,
                "production_system": None,
                "urban_rural": None
            })

        df_simulated = pd.DataFrame(simulated_records)
        X_simulated = preprocessor.transform(df_simulated)
        X_arr = X_simulated.toarray() if hasattr(X_simulated, "toarray") else np.array(X_simulated)

        mdr_probabilities = model.predict_proba(X_arr)[:, 1]
        
        ranked_options = []
        for index, agent in enumerate(POTENTIAL_ALTERNATIVES):
            mdr_prob = float(mdr_probabilities[index])
            success_prob = float(1.0 - mdr_prob)
            ranked_options.append({
                "antibiotic_agent": agent,
                "predicted_resistance_probability": mdr_prob,
                "estimated_efficacy_percentage": int(success_prob * 100)
            })
            
        ranked_options.sort(key=lambda x: x["estimated_efficacy_percentage"], reverse=True)

        return {
            "pathogen_code": payload.pathogen_code,
            "requested_resistance_pattern": payload.resistance_pattern,
            "primary_recommendation": ranked_options[0]["antibiotic_agent"],
            "ranked_treatment_alternatives": ranked_options,
            "clinical_annotation_note": "Evaluated and ranked dynamically using multi-agent model susceptibility inference vectors.",
            "user_role_context": payload.user_role,
            "regional_demographic_context": payload.county if payload.county else "National Registry baseline"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ranked model recommendation optimization simulation failed: {str(e)}"
        )
