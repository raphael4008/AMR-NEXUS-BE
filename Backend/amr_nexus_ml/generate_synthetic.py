import random
import uuid
import pandas as pd
from datetime import datetime

RESISTANCE_RATES = {
    ('eco', 'CIP'): 0.68,
    ('eco', 'AMP'): 0.80,
    ('kpn', 'CIP'): 0.55,
    ('sau', 'OXA'): 0.30,
}
SECTORS = ['HUMAN', 'ANIMAL']
SUBSECTORS = {'HUMAN': ['Inpatient', 'Outpatient'], 'ANIMAL': ['Poultry-Broiler', 'Poultry-Layer']}
PATHOGENS = ['eco', 'kpn', 'sau']
COUNTIES = ['Nairobi', 'Kiambu', 'Nakuru', 'Mombasa']
ANTIBIOTICS = ['CIP', 'AMP', 'GEN', 'CRO']
ANTIBIOTIC_CLASS_MAP = {'CIP': 'Fluoroquinolone', 'AMP': 'Penicillin', 'GEN': 'Aminoglycoside', 'CRO': 'Cephalosporin'}

def generate_record(i):
    sector = random.choice(SECTORS)
    sub_sector = random.choice(SUBSECTORS[sector])
    pathogen = random.choice(PATHOGENS)
    antibiotic = random.choice(ANTIBIOTICS)
    antibiotic_class = ANTIBIOTIC_CLASS_MAP.get(antibiotic, 'Unknown')
    rate = RESISTANCE_RATES.get((pathogen, antibiotic), 0.2)
    sir = 'R' if random.random() < rate else 'S'
    mdr_flag = random.random() < 0.25
    return {
        'record_id': str(uuid.uuid4()),
        'submission_type': 'SYNTHETIC',
        'pathogen_code': pathogen,
        'sir_result': sir,
        'antibiotic_code': antibiotic,
        'antibiotic_class': antibiotic_class,
        'sector': sector,
        'sub_sector': sub_sector,
        'specimen_type': 'Blood',
        'county': random.choice(COUNTIES),
        'sample_month': random.randint(1, 12),
        'mdr_flag': int(mdr_flag),
        'resistance_profile': 'MDR' if mdr_flag else 'Susceptible',
        'test_method': 'Disk diffusion',
        'patient_age_years': random.randint(1, 80) if sector == 'HUMAN' else None,
        'animal_species': 'Gallus gallus' if sector == 'ANIMAL' else None,
    }

def main():
    n_records = 5000
    print(f"Generating {n_records} synthetic records...")
    records = [generate_record(i) for i in range(n_records)]
    df = pd.DataFrame(records)
    output_path = "data/synthetic_amr_data.csv"
    # Ensure data directory exists
    import os
    os.makedirs("data", exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"✅ Saved {n_records} synthetic records to {output_path}")

if __name__ == "__main__":
    main()