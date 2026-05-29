-- database/schema.sql
-- WHO GLASS aligned AMR-Nexus schema for PostgreSQL / TimescaleDB
-- Includes v1.1 genomic metadata updates and pathogen normalization

CREATE TABLE amr_records (
    id SERIAL PRIMARY KEY,
    sample_collection_date TIMESTAMPTZ NOT NULL,
    sector VARCHAR(50) NOT NULL,
    pathogen_name VARCHAR(150) NOT NULL,
    antimicrobial_agent VARCHAR(150) NOT NULL,
    county VARCHAR(100) NOT NULL,
    sub_county VARCHAR(100),
    facility_type VARCHAR(100),
    result_value VARCHAR(50) NOT NULL,
    mic_value NUMERIC,
    is_synthetic INT DEFAULT 1,
    data_quality_score NUMERIC(4, 3),
    missing_fields JSONB,
    hl7_fhir_id VARCHAR(100),
    woah_reference VARCHAR(100),
    ncbi_tax_id INT NULL,
    sequencing_platform VARCHAR(100) NULL,
    assembly_id VARCHAR(100) NULL,
    accession_number VARCHAR(100) NULL,
    qc_status VARCHAR(50) NULL,
    patient_sex VARCHAR(50) NULL,
    patient_age_years INT NULL,
    admission_type VARCHAR(100) NULL,
    animal_species VARCHAR(100) NULL,
    production_system VARCHAR(100) NULL,
    infarm_compliant BOOLEAN DEFAULT FALSE,
    animuse_compliant BOOLEAN DEFAULT FALSE,
    glass_eligible BOOLEAN DEFAULT FALSE,
    woah_animal_aware_class VARCHAR(50) NULL,
    antimicrobial_residue_ppm NUMERIC(12, 6) NULL
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('amr_records', 'sample_collection_date');

-- Indexing for high-performance temporal and geographic queries
CREATE INDEX idx_geo_pathogen_time ON amr_records (county, pathogen_name, sample_collection_date DESC);
CREATE INDEX idx_amr_records_pathogen ON amr_records(pathogen_name);
CREATE INDEX idx_amr_records_county ON amr_records(county);
CREATE INDEX idx_amr_records_ncbi_tax_id_pathogen_name ON amr_records USING btree(ncbi_tax_id, pathogen_name);
CREATE INDEX idx_amr_records_compliance ON amr_records USING btree(infarm_compliant, animuse_compliant, glass_eligible);

-- Trigger routine to ensure pathogen_name is auto-normalized into standard formats
CREATE OR REPLACE FUNCTION tg_normalize_pathogen_name()
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

CREATE TRIGGER trg_normalize_pathogen_name
BEFORE INSERT OR UPDATE ON amr_records
FOR EACH ROW
EXECUTE FUNCTION tg_normalize_pathogen_name();

CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    amr_record_id INT NOT NULL,
    detection_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    anomaly_score NUMERIC NOT NULL,
    hotspot_magnitude NUMERIC NOT NULL,
    feature_importance JSONB,
    FOREIGN KEY (amr_record_id) REFERENCES amr_records(id) ON DELETE CASCADE
);

CREATE INDEX idx_alerts_record_id ON alerts(amr_record_id);

CREATE TABLE guidance (
    id SERIAL PRIMARY KEY,
    alert_id INT NOT NULL,
    generation_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    role_target VARCHAR(100) NOT NULL,
    content_markdown TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING',
    FOREIGN KEY (alert_id) REFERENCES alerts(id) ON DELETE CASCADE
);

CREATE INDEX idx_guidance_alert_id ON guidance(alert_id);
