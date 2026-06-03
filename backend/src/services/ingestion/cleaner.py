import json
import pandas as pd
from typing import List, Tuple, Dict, Any

class DataCleaner:
    def __init__(self):
        # Enforcing non-negotiable elements for a valid AMR signal
        self.critical_fields = [
            "pathogen_name", 
            "antimicrobial_agent", 
            "result_value", 
            "county"
        ]

    def process_dirty_data(self, raw_payload: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Validates, calculates quality scores, imputes non-critical fields, 
        and hard-rejects rows missing non-negotiable fields.
        """
        if not raw_payload:
            return [], []

        df = pd.DataFrame(raw_payload)
        
        if df.empty:
            return [], []
            
        # 1. Calculate Data Quality Score (0.0 to 1.0)
        df['data_quality_score'] = 1.0 - df.isnull().mean(axis=1)

        # 2. Track Missing Fields for Provenance (Vectorized using numpy)
        null_mask = df.isnull()
        df['missing_fields'] = [
            json.dumps(cols) for cols in 
            [null_mask.columns[mask].tolist() for mask in null_mask.to_numpy()]
        ]

        # 3. Impute non-critical fields
        if 'facility_type' in df.columns:
            df['facility_type'] = df['facility_type'].fillna("Unknown/Not Reported")
            
        if 'sub_county' in df.columns and 'county' in df.columns:
            # Impute sub_county based on the statistical mode of the respective county (Vectorized)
            county_modes = df.groupby('county')['sub_county'].agg(
                lambda x: x.mode()[0] if not x.mode().empty else "Unknown"
            )
            df['sub_county'] = df['sub_county'].fillna(df['county'].map(county_modes))
            df['sub_county'] = df['sub_county'].fillna("Unknown")

        # String Normalization for Pathogens (covers case-insensitive variants)
        if 'pathogen_name' in df.columns:
            def _normalize_pathogen(v):
                if not isinstance(v, str):
                    return v
                vl = v.lower()
                if 'e. coli' in vl or 'e coli' in vl:
                    return 'Escherichia coli'
                if 's. aureus' in vl or 's aureus' in vl:
                    return 'Staphylococcus aureus'
                if 'k. pneumoniae' in vl or 'k pneumoniae' in vl:
                    return 'Klebsiella pneumoniae'
                return v
            df['pathogen_name'] = df['pathogen_name'].apply(_normalize_pathogen)

        # SIR Normalization — maps full-word values to single-char codes
        # Prevents CHAR(1) data truncation in PostgreSQL production environment
        _SIR_MAP = {
            'resistant': 'R', 'susceptible': 'S', 'intermediate': 'I',
            'sensitive': 'S', 'nonsusceptible': 'R',
        }
        if 'result_value' in df.columns:
            df['result_value'] = df['result_value'].apply(
                lambda v: _SIR_MAP.get(str(v).lower().strip(), v) if pd.notna(v) else v
            )

        # 4. Isolate critical failures
        for col in self.critical_fields:
            if col not in df.columns:
                df[col] = None

        critical_mask = df[self.critical_fields].isnull().any(axis=1)
        rejected_df = df[critical_mask]
        clean_df = df[~critical_mask]

        return clean_df.to_dict(orient='records'), rejected_df.to_dict(orient='records')
