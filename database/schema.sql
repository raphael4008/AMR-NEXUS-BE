-- database/schema.sql
-- WHO GLASS aligned AMR-Nexus schema for PostgreSQL / TimescaleDB

CREATE TABLE amr_records (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
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
    woah_reference VARCHAR(100)
);

-- Indexing for high-performance temporal and geographic queries
CREATE INDEX idx_amr_records_timestamp ON amr_records(timestamp);
CREATE INDEX idx_amr_records_pathogen ON amr_records(pathogen_name);
CREATE INDEX idx_amr_records_county ON amr_records(county);

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
