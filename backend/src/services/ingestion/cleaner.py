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
        
        # 1. Calculate Data Quality Score (0.0 to 1.0)
        df['data_quality_score'] = 1.0 - df.isnull().mean(axis=1)

        # 2. Track Missing Fields for Provenance
        df['missing_fields'] = df.apply(
            lambda row: json.dumps(row.index[row.isnull()].tolist()), axis=1
        )

        # 3. Impute non-critical fields
        if 'facility_type' in df.columns:
            df['facility_type'] = df['facility_type'].fillna("Unknown/Not Reported")
            
        if 'sub_county' in df.columns and 'county' in df.columns:
            # Impute sub_county based on the statistical mode of the respective county
            df['sub_county'] = df.groupby('county')['sub_county'].transform(
                lambda x: x.fillna(x.mode()[0] if not x.mode().empty else "Unknown")
            )

        # 4. Isolate critical failures
        for col in self.critical_fields:
            if col not in df.columns:
                df[col] = None

        critical_mask = df[self.critical_fields].isnull().any(axis=1)
        rejected_df = df[critical_mask]
        clean_df = df[~critical_mask]

        return clean_df.to_dict(orient='records'), rejected_df.to_dict(orient='records')
