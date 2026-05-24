import pandas as pd
import numpy as np
from typing import Tuple, List

class DataCleaner:
    def __init__(self, threshold: float = 0.4):
        """
        :param threshold: Percentage of missing values allowed before 
                          marking a record as 'Critical Failure' (default 40%).
        """
        self.threshold = threshold
        # Non-negotiable fields for a valid AMR signal
        self.critical_fields = ["pathogen_name", "antimicrobial_agent", "result_value", "county"]

    def calculate_quality_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculates a score from 0.0 to 1.0 based on row completeness."""
        return 1.0 - df.isnull().mean(axis=1)

    def process_dirty_data(self, raw_data: List[dict]) -> Tuple[pd.DataFrame, List[dict]]:
        if not raw_data:
            return pd.DataFrame(), []

        df = pd.DataFrame(raw_data)

        # 1. Calculate Initial Quality Scores
        df['data_quality_score'] = self.calculate_quality_score(df)

        # 2. Identify Critical Failures (Missing non-negotiable fields)
        # Ensure all critical columns exist (some payloads may omit them entirely)
        for col in self.critical_fields:
            if col not in df.columns:
                df[col] = None
        critical_missing = df[df[self.critical_fields].isnull().any(axis=1)]
        
        # 3. Perform Imputation for non-critical fields
        # Example: If facility_type is missing, label as 'Unknown/Not Reported'
        if 'facility_type' in df.columns:
            df['facility_type'] = df['facility_type'].fillna("Unknown/Not Reported")
            
        # Example: Mode imputation for sub-county based on county
        if 'sub_county' in df.columns:
            df['sub_county'] = df.groupby('county')['sub_county'].transform(
                lambda x: x.fillna(x.mode()[0] if not x.mode().empty else "Unknown")
            )

        # 4. Track what was changed for transparency (Module 1 requirement)
        df['missing_fields'] = df.apply(
            lambda row: row.index[row.isnull()].tolist(), axis=1
        )

        return df.drop(critical_missing.index), critical_missing.to_dict(orient='records')
