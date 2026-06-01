-- database/schema_v1.2.sql
-- WHO GLASS aligned AMR-Nexus schema for PostgreSQL / TimescaleDB
-- Includes v1.2 genomic metadata updates, optimized storage, and UUIDs

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE amr_isolate_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sample_collection_date TIMESTAMPTZ NOT NULL,
    sector VARCHAR(20) NOT NULL, -- HUMAN, ANIMAL, ENVIRONMENT
    pathogen_name VARCHAR(100) NOT NULL,
    antimicrobial_agent VARCHAR(100) NOT NULL,
    county VARCHAR(50) NOT NULL,
    sub_county VARCHAR(50),
    facility_type VARCHAR(50),
    result_value CHAR(1) NOT NULL, -- S, I, R
    mic_value NUMERIC(6, 2),
    is_synthetic INT DEFAULT 1,
    data_quality_score NUMERIC(4, 3),
    missing_fields JSONB,
    hl7_fhir_id VARCHAR(50),
    woah_reference VARCHAR(50),
    ncbi_tax_id INT NULL,
    sequencing_platform VARCHAR(50) NULL,
    assembly_id VARCHAR(50) NULL,
    accession_number VARCHAR(50) NULL,
    qc_status VARCHAR(20) NULL,
    patient_sex VARCHAR(10) NULL,
    patient_age_years INT NULL,
    admission_type VARCHAR(50) NULL,
    animal_species VARCHAR(50) NULL,
    production_system VARCHAR(50) NULL,
    infarm_compliant BOOLEAN DEFAULT FALSE,
    animuse_compliant BOOLEAN DEFAULT FALSE,
    glass_eligible BOOLEAN DEFAULT FALSE,
    woah_animal_aware_class VARCHAR(50) NULL,
    antimicrobial_residue_ppm NUMERIC(10, 4) NULL
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('amr_isolate_records', 'sample_collection_date', if_not_exists => TRUE);

-- Indexing for high-performance temporal and geographic queries
CREATE INDEX idx_geo_pathogen_time_v2 ON amr_isolate_records (county, pathogen_name, sample_collection_date DESC);
CREATE INDEX idx_amr_isolate_records_pathogen ON amr_isolate_records(pathogen_name);
CREATE INDEX idx_amr_isolate_records_county ON amr_isolate_records(county);
CREATE INDEX idx_amr_isolate_records_compliance ON amr_isolate_records USING btree(infarm_compliant, animuse_compliant, glass_eligible);
CREATE INDEX idx_geo_sector ON amr_isolate_records (county, sub_county, sector);
CREATE INDEX idx_time_series ON amr_isolate_records (
    EXTRACT(YEAR FROM sample_collection_date),
    EXTRACT(MONTH FROM sample_collection_date),
    EXTRACT(WEEK FROM sample_collection_date)
);

-- Trigger routine to ensure pathogen_name is auto-normalized into standard formats
CREATE OR REPLACE FUNCTION tg_normalize_pathogen_name_v2()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.pathogen_name ILIKE '%E. coli%' OR NEW.pathogen_name ILIKE '%E coli%' THEN
        NEW.pathogen_name := 'Escherichia coli';
    ELSIF NEW.pathogen_name ILIKE '%S. aureus%' OR NEW.pathogen_name ILIKE '%S aureus%' THEN
        NEW.pathogen_name := 'Staphylococcus aureus';
    ELSIF NEW.pathogen_name ILIKE '%K. pneumoniae%' OR NEW.pathogen_name ILIKE '%K pneumoniae%' THEN
        NEW.pathogen_name := 'Klebsiella pneumoniae';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_normalize_pathogen_name_v2
BEFORE INSERT OR UPDATE ON amr_isolate_records
FOR EACH ROW
EXECUTE FUNCTION tg_normalize_pathogen_name_v2();

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    amr_isolate_record_id UUID NOT NULL,
    detection_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    anomaly_score NUMERIC NOT NULL,
    hotspot_magnitude NUMERIC NOT NULL,
    feature_importance JSONB,
    FOREIGN KEY (amr_isolate_record_id) REFERENCES amr_isolate_records(id) ON DELETE CASCADE
);

CREATE INDEX idx_alerts_isolate_record_id ON alerts(amr_isolate_record_id);

CREATE TABLE guidance_briefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id UUID NOT NULL,
    generation_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    role_target VARCHAR(50) NOT NULL,
    content_markdown TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    FOREIGN KEY (alert_id) REFERENCES alerts(id) ON DELETE CASCADE
);

CREATE INDEX idx_guidance_briefs_alert_id ON guidance_briefs(alert_id);
