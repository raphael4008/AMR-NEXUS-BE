-- WHO GLASS / FAO InFARM / WOAH ANIMUSE / WHO GAP-AMR (2026–2036) aligned
-- AMR-Nexus Kenya — 3-Tier Normalized Schema for PostgreSQL / TimescaleDB
-- Track: database/feature-migration-v1.3

-- ─────────────────────────────────────────────────────────────────────────────
-- EXTENSIONS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─────────────────────────────────────────────────────────────────────────────
-- TIER 1: CENTRAL FACT TABLE — amr_isolate_records
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS amr_isolate_records (
    -- Primary Identity (Composite Key configured for TimescaleDB Partitioning)
    record_id               UUID DEFAULT gen_random_uuid(),
    sample_collection_date  TIMESTAMPTZ NOT NULL,
    record_version          INTEGER DEFAULT 1,
    data_source_id          VARCHAR(50) NULL,
    created_at              TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- ── 3.4 One Health Sector ──────────────────────────────────────────────
    sector                  VARCHAR(20) NOT NULL CHECK (sector IN ('HUMAN', 'ANIMAL', 'ENVIRONMENT')),
    sub_sector              VARCHAR(50) NULL,

    -- ── 3.2 Pathogen Taxonomy ──────────────────────────────────────────────
    pathogen_name           VARCHAR(150) NOT NULL,
    pathogen_code           VARCHAR(30)  NULL,
    ncbi_taxonomy_id        INTEGER      NULL,
    genus                   VARCHAR(100) NULL,
    species                 VARCHAR(100) NULL,
    resistance_profile      VARCHAR(50)  NOT NULL DEFAULT 'Unknown' CHECK (resistance_profile IN ('MDR', 'XDR', 'PDR', 'Susceptible', 'Unknown')),
    mdr_flag                BOOLEAN      DEFAULT FALSE,

    -- ── 3.3 Antimicrobial Profile & AST ────────────────────────────────────
    antibiotic_code         VARCHAR(20)  NULL,
    antibiotic_name         VARCHAR(100) NOT NULL,
    antibiotic_class        VARCHAR(100) NULL,
    mic_value               NUMERIC(10, 4) NULL,
    mic_operator            CHAR(2)      NULL,
    disk_diffusion_mm       INTEGER      NULL,
    sir_result              CHAR(1) NOT NULL CHECK (sir_result IN ('S', 'I', 'R')),
    breakpoint_standard     VARCHAR(20)  NULL,
    test_method             VARCHAR(50)  NULL,

    -- ── 3.5 Geography & Facilities ─────────────────────────────────────────
    country_code            CHAR(3)      DEFAULT 'KEN',
    country_name            VARCHAR(100) DEFAULT 'Kenya',
    region                  VARCHAR(100) NULL,
    county                  VARCHAR(50)  NOT NULL,
    sub_county              VARCHAR(50)  NULL,
    facility_id             VARCHAR(50)  NULL,
    facility_type           VARCHAR(50)  NULL,
    urban_rural             VARCHAR(10)  NULL,
    latitude                NUMERIC(9, 6) NULL,
    longitude               NUMERIC(9, 6) NULL,

    -- ── Dataset-Specific Dashboard Indicators ──────────────────────────────
    specimen_type           VARCHAR(100)  NULL,
    sample_source           VARCHAR(100)  NULL,
    resistance_rate         NUMERIC(5, 4) NULL,
    resistance_percent      NUMERIC(6, 2) NULL,
    classification          VARCHAR(20)   NULL, -- Legacy UI Fallback
    sample_size             INTEGER       NULL,
    hospitalised            VARCHAR(30)   NULL,
    outcome                 VARCHAR(50)   NULL,
    reported_by             VARCHAR(100)  NULL,

    -- ── Temporal Partitioning ──────────────────────────────────────────────
    sample_year             SMALLINT GENERATED ALWAYS AS (EXTRACT(YEAR  FROM (sample_collection_date AT TIME ZONE 'UTC'))::SMALLINT) STORED,
    sample_month            SMALLINT GENERATED ALWAYS AS (EXTRACT(MONTH FROM (sample_collection_date AT TIME ZONE 'UTC'))::SMALLINT) STORED,
    sample_week             SMALLINT GENERATED ALWAYS AS (EXTRACT(WEEK  FROM (sample_collection_date AT TIME ZONE 'UTC'))::SMALLINT) STORED,
    result_date             DATE         NULL,
    turnaround_days         INTEGER      NULL,
    
    -- ── Data Integrity ─────────────────────────────────────────────────────
    data_quality_score      NUMERIC(4, 3) DEFAULT 1.0,
    missing_fields          JSONB         NULL,
    submission_type         VARCHAR(30)   NOT NULL DEFAULT 'SYNTHETIC' CHECK (submission_type IN ('SYNTHETIC', 'REAL', 'VALIDATED', 'IMPORTED')),

    -- ── 3.7 Patient/Host Demographics ──────────────────────────────────────
    patient_sex             VARCHAR(10)  NULL,
    patient_age_years       NUMERIC(5, 1) NULL,
    patient_age_group       VARCHAR(20)  NULL,
    ward_type               VARCHAR(50)  NULL,
    admission_type          VARCHAR(50)  NULL,
    clinical_indication     VARCHAR(150) NULL,
    prior_antibiotic_exposure BOOLEAN    NULL,
    infection_origin        VARCHAR(20)  NULL,

    -- ── GAP-AMR Disaggregation — Animal ───────────────────────────────────
    animal_species          VARCHAR(100) NULL,
    production_system       VARCHAR(100) NULL,

    -- ── 3.8 GLASS / WHONET / DHIS2 Interoperability ───────────────────────
    glass_specimen_code     VARCHAR(10)  NULL,
    glass_pathogen_code     VARCHAR(10)  NULL,
    glass_antibiotic_code   VARCHAR(10)  NULL,
    whonet_org_code         VARCHAR(20)  NULL,
    dhis2_org_unit          VARCHAR(50)  NULL,
    dhis2_data_element      VARCHAR(50)  NULL,
    glass_eligible          BOOLEAN DEFAULT FALSE,

    -- ── 3.10 Genomic Metadata ──────────────────────────────────────────────
    hl7_fhir_id             VARCHAR(50) NULL,
    woah_reference          VARCHAR(50) NULL,
    sequencing_platform     VARCHAR(100) NULL,
    assembly_id             VARCHAR(100) NULL,
    accession_number        VARCHAR(100) NULL,
    sequencing_date         DATE         NULL,
    coverage_depth          NUMERIC(6, 2) NULL,
    qc_status               VARCHAR(50) NULL,

    -- ── Compliance Flags ──────────────────────────────────────────────────
    infarm_compliant        BOOLEAN DEFAULT FALSE,
    animuse_compliant       BOOLEAN DEFAULT FALSE,
    woah_animal_aware_class VARCHAR(50)  NULL,
    antimicrobial_residue_ppm NUMERIC(10, 4) NULL,

    -- ── 3.9 AI Model Output Fields ─────────────────────────────────────────
    anomaly_score           NUMERIC(5, 4) NULL,
    anomaly_flag            BOOLEAN DEFAULT FALSE,
    forecast_cluster_id     VARCHAR(50) NULL,
    alert_triggered         BOOLEAN DEFAULT FALSE,
    alert_timestamp         TIMESTAMPTZ NULL,
    shap_top_feature        VARCHAR(100) NULL,
    shap_value              NUMERIC(8, 4) NULL,
    model_version           VARCHAR(20) NULL,

    is_synthetic            SMALLINT DEFAULT 1 CHECK (is_synthetic IN (0, 1)),

    -- Composite Primary Key Enforces TimescaleDB Partition Integrity
    PRIMARY KEY (record_id, sample_collection_date)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable(
    'amr_isolate_records',
    'sample_collection_date',
    if_not_exists => TRUE,
    migrate_data   => TRUE
);

-- ── Indices ──────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_amr_geo_sector     ON amr_isolate_records USING BTREE (county, sub_county, sector);
CREATE INDEX IF NOT EXISTS idx_amr_time_pathogen  ON amr_isolate_records (sample_collection_date DESC, pathogen_name);
CREATE INDEX IF NOT EXISTS idx_amr_coordinates    ON amr_isolate_records (latitude, longitude) WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_amr_anomaly        ON amr_isolate_records (anomaly_flag, anomaly_score);
CREATE INDEX IF NOT EXISTS idx_amr_submission     ON amr_isolate_records (submission_type);


-- ─────────────────────────────────────────────────────────────────────────────
-- TIER 2: REFERENCE DIMENSION TABLE — resistance_genes
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS resistance_genes (
    gene_id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gene_name                VARCHAR(100) NOT NULL UNIQUE,
    gene_family              VARCHAR(100) NULL,
    gene_variant             VARCHAR(50)  NULL,
    resistance_mechanism     VARCHAR(150) NULL,
    drug_class_target        VARCHAR(200) NULL,
    phenotype                VARCHAR(200) NULL,
    detection_method         VARCHAR(100) NULL,
    mobile_element           BOOLEAN DEFAULT FALSE,
    mge_type                 VARCHAR(50)  NULL,
    horizontal_transfer_risk VARCHAR(10)  NULL,
    first_reported_year      INTEGER      NULL,
    first_reported_region    VARCHAR(100) NULL,
    kenya_reported           BOOLEAN DEFAULT FALSE,
    ea_reported              BOOLEAN DEFAULT FALSE,
    glass_relevant           BOOLEAN NOT NULL DEFAULT FALSE,
    who_priority_flag        BOOLEAN NOT NULL DEFAULT FALSE,
    notes                    TEXT         NULL,
    created_at               TIMESTAMPTZ  DEFAULT CURRENT_TIMESTAMP,
    updated_at               TIMESTAMPTZ  DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_resistance_genes_name ON resistance_genes (gene_name);
CREATE INDEX IF NOT EXISTS idx_resistance_genes_who  ON resistance_genes (who_priority_flag) WHERE who_priority_flag = TRUE;

INSERT INTO resistance_genes (gene_name, gene_family, resistance_mechanism, drug_class_target, phenotype, detection_method, mobile_element, horizontal_transfer_risk, kenya_reported, ea_reported, glass_relevant, who_priority_flag)
VALUES
    ('blaNDM-1',    'bla',  'Enzymatic hydrolysis',          'Carbapenems',     'Carbapenemase',           'PCR / WGS', TRUE, 'HIGH', TRUE, TRUE, TRUE,  TRUE),
    ('mcr-1',       'mcr',  'Target modification',           'Polymyxins',      'MCR',                     'PCR / WGS', TRUE, 'HIGH', TRUE, TRUE, TRUE,  TRUE),
    ('mecA',        'mec',  'Altered PBP target',            'Beta-lactams',    'MRSA',                    'PCR / WGS', TRUE, 'HIGH', TRUE, TRUE, TRUE,  TRUE),
    ('blaCTX-M-15', 'bla',  'Enzymatic hydrolysis',          '3rd-gen Cephalosporins', 'ESBL',             'PCR / WGS', TRUE, 'HIGH', TRUE, TRUE, TRUE,  TRUE)
ON CONFLICT (gene_name) DO NOTHING;


-- ─────────────────────────────────────────────────────────────────────────────
-- TIER 3: JUNCTION TABLE — isolate_resistance_genes (Many-to-Many)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS isolate_resistance_genes (
    link_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id        UUID NOT NULL,
    sample_date      TIMESTAMPTZ NOT NULL,
    gene_id          UUID NOT NULL REFERENCES resistance_genes(gene_id) ON DELETE RESTRICT,
    detection_method VARCHAR(100) NULL,
    copies_detected  INTEGER NULL,
    co_carriage_flag BOOLEAN DEFAULT FALSE,
    confirmed_by_wgs BOOLEAN DEFAULT FALSE,
    notes            TEXT NULL,
    detected_at      DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (record_id, sample_date) REFERENCES amr_isolate_records(record_id, sample_collection_date) ON DELETE CASCADE,
    UNIQUE (record_id, gene_id)
);

CREATE INDEX IF NOT EXISTS idx_irg_record_id ON isolate_resistance_genes (record_id);
CREATE INDEX IF NOT EXISTS idx_irg_gene_id   ON isolate_resistance_genes (gene_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- SUPPORTING TABLES: alerts, guidance_briefs
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    amr_isolate_record_id UUID NOT NULL,
    sample_date           TIMESTAMPTZ NOT NULL,
    detection_timestamp   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    anomaly_score         NUMERIC NOT NULL,
    hotspot_magnitude     NUMERIC NOT NULL,
    feature_importance    JSONB NULL,
    status                VARCHAR(50) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'NOTIFIED')),
    FOREIGN KEY (amr_isolate_record_id, sample_date) REFERENCES amr_isolate_records(record_id, sample_collection_date) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS guidance_briefs (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id              UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    generation_timestamp  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    role_target           VARCHAR(50) NOT NULL CHECK (role_target IN ('National Coordinator', 'County Veterinarian')),
    content_markdown      TEXT NOT NULL,
    status                VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED'))
);


-- ─────────────────────────────────────────────────────────────────────────────
-- PATHOGEN NORMALIZATION TRIGGER FUNCTION
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION tg_normalize_pathogen_name()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.pathogen_name ILIKE '%E. coli%' OR NEW.pathogen_name ILIKE '%E coli%' THEN
        NEW.pathogen_name := 'Escherichia coli';
    ELSIF NEW.pathogen_name ILIKE '%S. aureus%' OR NEW.pathogen_name ILIKE '%S aureus%' THEN
        NEW.pathogen_name := 'Staphylococcus aureus';
    ELSIF NEW.pathogen_name ILIKE '%K. pneumoniae%' OR NEW.pathogen_name ILIKE '%K pneumoniae%' THEN
        NEW.pathogen_name := 'Klebsiella pneumoniae';
    ELSIF NEW.pathogen_name ILIKE '%A. baumannii%' OR NEW.pathogen_name ILIKE '%A baumannii%' THEN
        NEW.pathogen_name := 'Acinetobacter baumannii';
    ELSIF NEW.pathogen_name ILIKE '%P. aeruginosa%' OR NEW.pathogen_name ILIKE '%P aeruginosa%' THEN
        NEW.pathogen_name := 'Pseudomonas aeruginosa';
    ELSIF NEW.pathogen_name ILIKE '%S. typhi%' OR NEW.pathogen_name ILIKE '%S typhi%' THEN
        NEW.pathogen_name := 'Salmonella typhi';
    ELSIF NEW.pathogen_name ILIKE '%S. enterica%' OR NEW.pathogen_name ILIKE '%S enterica%' THEN
        NEW.pathogen_name := 'Salmonella enterica';
    ELSIF NEW.pathogen_name ILIKE '%S. pneumoniae%' OR NEW.pathogen_name ILIKE '%S pneumoniae%' THEN
        NEW.pathogen_name := 'Streptococcus pneumoniae';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_normalize_pathogen_name
BEFORE INSERT OR UPDATE ON amr_isolate_records
FOR EACH ROW
EXECUTE FUNCTION tg_normalize_pathogen_name();