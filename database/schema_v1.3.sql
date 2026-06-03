-- database/schema_v1.3.sql
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
-- Maps all 10 previously unmapped dataset variables and dataset-specific
-- indicators. Source of truth for all One Health isolate surveillance data.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS amr_isolate_records (
    -- Primary Identity
    record_id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- ── One Health Sector ──────────────────────────────────────────────────
    sector                  VARCHAR(20) NOT NULL CHECK (sector IN ('HUMAN', 'ANIMAL', 'ENVIRONMENT')),

    -- ── Pathogen Taxonomy (Unmapped Variables 1–3) ─────────────────────────
    pathogen_name           VARCHAR(150) NOT NULL,
    pathogen_code           VARCHAR(30)  NULL,
    ncbi_taxonomy_id        INTEGER      NULL,

    -- ── Antimicrobial Profile (Unmapped Variables 4–6) ────────────────────
    antibiotic_code         VARCHAR(20)  NULL,
    antibiotic_name         VARCHAR(100) NOT NULL,
    antibiotic_class        VARCHAR(100) NULL,

    -- ── Resistance Result (Unmapped Variables 7–8) ────────────────────────
    mic_value               NUMERIC(10, 4) NULL,
    sir_result              CHAR(1) NOT NULL CHECK (sir_result IN ('S', 'I', 'R')),

    -- ── Geography (Unmapped Variables 9–10) ───────────────────────────────
    county                  VARCHAR(50) NOT NULL,
    sub_county              VARCHAR(50) NULL,

    -- ── Dataset-Specific Indicators ────────────────────────────────────────
    latitude                NUMERIC(9, 6) NULL,
    longitude               NUMERIC(9, 6) NULL,
    specimen_type           VARCHAR(100)  NULL,
    resistance_rate         NUMERIC(5, 4) NULL,   -- decimal proportion e.g. 0.6850
    resistance_percent      NUMERIC(6, 2) NULL,   -- human-readable e.g. 68.50
    classification          VARCHAR(20)   NULL CHECK (classification IN ('MDR', 'XDR', 'PDR', 'Susceptible', NULL)),
    sample_size             INTEGER       NULL,
    hospitalised            VARCHAR(30)   NULL,
    outcome                 VARCHAR(50)   NULL,
    reported_by             VARCHAR(100)  NULL,

    -- ── Temporal Partitioning ──────────────────────────────────────────────
    sample_collection_date  TIMESTAMPTZ NOT NULL,
    sample_year             SMALLINT GENERATED ALWAYS AS (EXTRACT(YEAR  FROM sample_collection_date)::SMALLINT) STORED,
    sample_month            SMALLINT GENERATED ALWAYS AS (EXTRACT(MONTH FROM sample_collection_date)::SMALLINT) STORED,
    sample_week             SMALLINT GENERATED ALWAYS AS (EXTRACT(WEEK  FROM sample_collection_date)::SMALLINT) STORED,

    -- ── Data Integrity ─────────────────────────────────────────────────────
    data_quality_score      NUMERIC(4, 3) DEFAULT 1.0,
    missing_fields          JSONB         NULL,
    submission_type         VARCHAR(30)   NOT NULL DEFAULT 'SYNTHETIC' CHECK (submission_type IN ('SYNTHETIC', 'REAL', 'IMPORTED')),

    -- ── GAP-AMR Disaggregation — Human ────────────────────────────────────
    patient_sex             VARCHAR(10)  NULL,
    patient_age_years       INTEGER      NULL,
    admission_type          VARCHAR(50)  NULL,
    clinical_indication     VARCHAR(150) NULL,

    -- ── GAP-AMR Disaggregation — Animal ───────────────────────────────────
    animal_species          VARCHAR(100) NULL,
    production_system       VARCHAR(100) NULL,

    -- ── Interoperability & Genomic Metadata ───────────────────────────────
    hl7_fhir_id             VARCHAR(50) NULL,
    woah_reference          VARCHAR(50) NULL,
    sequencing_platform     VARCHAR(50) NULL,
    assembly_id             VARCHAR(50) NULL,
    accession_number        VARCHAR(50) NULL,
    qc_status               VARCHAR(20) NULL,

    -- ── Compliance Flags ──────────────────────────────────────────────────
    infarm_compliant        BOOLEAN DEFAULT FALSE,
    animuse_compliant       BOOLEAN DEFAULT FALSE,
    glass_eligible          BOOLEAN DEFAULT FALSE,  -- GLASS-compatible reporting flag (not universal)
    woah_animal_aware_class VARCHAR(50)  NULL,
    antimicrobial_residue_ppm NUMERIC(10, 4) NULL,

    -- ── Record Provenance ─────────────────────────────────────────────────
    is_synthetic            SMALLINT DEFAULT 1 CHECK (is_synthetic IN (0, 1)),
    created_at              TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Convert to TimescaleDB hypertable (partition by time for high-throughput queries)
SELECT create_hypertable(
    'amr_isolate_records',
    'sample_collection_date',
    if_not_exists => TRUE,
    migrate_data   => TRUE
);

-- ── Indices ────────────────────────────────────────────────────────────────────
-- Composite BTREE for geographic disaggregation queries (eliminates hardcoded lookups)
CREATE INDEX IF NOT EXISTS idx_amr_geo_sector     ON amr_isolate_records USING BTREE (county, sub_county, sector);
-- Temporal query optimization
CREATE INDEX IF NOT EXISTS idx_amr_time_pathogen  ON amr_isolate_records (sample_collection_date DESC, pathogen_name);
-- Heatmap geometry queries (lat/lon coordinate lookups)
CREATE INDEX IF NOT EXISTS idx_amr_coordinates    ON amr_isolate_records (latitude, longitude) WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
-- Compliance analytics
CREATE INDEX IF NOT EXISTS idx_amr_compliance     ON amr_isolate_records USING BTREE (infarm_compliant, animuse_compliant, glass_eligible);
-- Pathogen fast-lookup
CREATE INDEX IF NOT EXISTS idx_amr_pathogen       ON amr_isolate_records (pathogen_name, sir_result);
-- Resistance classification fast-lookup
CREATE INDEX IF NOT EXISTS idx_amr_classification ON amr_isolate_records (classification, county);


-- ─────────────────────────────────────────────────────────────────────────────
-- TIER 2: REFERENCE DIMENSION TABLE — resistance_genes
-- Priority ARG catalog. Pre-populated with 15 WHO-priority resistance genes.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS resistance_genes (
    gene_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gene_name            VARCHAR(100) NOT NULL UNIQUE,
    gene_family          VARCHAR(100) NULL,
    resistance_mechanism VARCHAR(150) NULL,
    drug_class_target    VARCHAR(150) NULL,
    phenotype            VARCHAR(200) NULL,
    detection_method     VARCHAR(100) NULL,
    glass_relevant       BOOLEAN NOT NULL DEFAULT FALSE,
    who_priority_flag    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at           TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_resistance_genes_name ON resistance_genes (gene_name);
CREATE INDEX IF NOT EXISTS idx_resistance_genes_who  ON resistance_genes (who_priority_flag) WHERE who_priority_flag = TRUE;

-- Pre-populate with 15 WHO/GLASS Priority Antimicrobial Resistance Genes
INSERT INTO resistance_genes (gene_name, gene_family, resistance_mechanism, drug_class_target, phenotype, detection_method, glass_relevant, who_priority_flag)
VALUES
    ('blaNDM-1',    'MBL (Metallo-β-lactamase)',  'Enzymatic hydrolysis',          'Carbapenems / β-lactams',     'Carbapenem resistance',           'PCR / WGS',     TRUE,  TRUE),
    ('mcr-1',       'MCR Phosphoethanolamine transferase', 'Lipid A modification', 'Colistin (Polymyxins)',         'Colistin resistance (transferable)', 'PCR / WGS', TRUE,  TRUE),
    ('mecA',        'PBP2a',                       'Altered PBP target',            'β-lactams / Methicillin',     'MRSA phenotype',                  'PCR / WGS',     TRUE,  TRUE),
    ('blaCTX-M-15', 'ESBL (CTX-M group 1)',        'Enzymatic hydrolysis',          'Cephalosporins (3rd gen)',     'ESBL-producing Enterobacteriaceae', 'PCR / WGS',   TRUE,  TRUE),
    ('blaKPC-2',    'KPC serine carbapenemase',    'Enzymatic hydrolysis',          'Carbapenems / β-lactams',     'Carbapenem-resistant Klebsiella',  'PCR / WGS',     TRUE,  TRUE),
    ('blaOXA-48',   'OXA-type carbapenemase',      'Enzymatic hydrolysis',          'Carbapenems / Penicillins',   'Carbapenem resistance',           'PCR / WGS',     TRUE,  TRUE),
    ('vanA',        'Vancomycin resistance operon', 'Target modification (D-Ala)',  'Glycopeptides / Vancomycin',  'VRE phenotype (high-level)',       'PCR / WGS',     TRUE,  TRUE),
    ('tetM',        'Tet efflux/ribosome protection', 'Ribosomal protection',       'Tetracyclines',               'Broad-spectrum tet resistance',   'PCR / WGS',     FALSE, TRUE),
    ('sul1',        'Sulfonamide resistance',       'Target bypass (DHPS alt)',      'Sulfonamides',                'Sulfonamide resistance',          'PCR / WGS',     FALSE, TRUE),
    ('qnrS',        'Quinolone resistance (PMQR)', 'Gyrase target protection',      'Fluoroquinolones',            'Low-level quinolone resistance',  'PCR / WGS',     TRUE,  TRUE),
    ('aph(3'')-Ia', 'APH aminoglycoside kinase',   'Enzymatic phosphorylation',     'Aminoglycosides (Kanamycin)', 'Aminoglycoside resistance',       'PCR / WGS',     FALSE, FALSE),
    ('blaTEM-1',    'TEM β-lactamase (class A)',   'Enzymatic hydrolysis',          'Penicillins / Ampicillin',   'Ampicillin resistance',           'PCR / WGS',     FALSE, FALSE),
    ('blaSHV-1',    'SHV β-lactamase (class A)',   'Enzymatic hydrolysis',          'Penicillins',                 'Narrow-spectrum β-lactam resist.','PCR / WGS',     FALSE, FALSE),
    ('armA',        'Ribosomal methyltransferase', 'Ribosomal methylation (16S)',   'Aminoglycosides',             'Pan-aminoglycoside resistance',   'WGS',           TRUE,  TRUE),
    ('cfr',         'Cfr methyltransferase',       '23S rRNA methylation',          'Phenicols/Lincosamides/Oxaz', 'PhLOPSA cross-resistance',        'PCR / WGS',     TRUE,  TRUE)
ON CONFLICT (gene_name) DO NOTHING;


-- ─────────────────────────────────────────────────────────────────────────────
-- TIER 3: JUNCTION TABLE — isolate_resistance_genes (Many-to-Many)
-- Links isolate records to their specific detected resistance genes.
-- Replaces JSONB blob storage in genomic_signals with normalized linkages.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS isolate_resistance_genes (
    link_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id        UUID NOT NULL REFERENCES amr_isolate_records(record_id) ON DELETE CASCADE,
    gene_id          UUID NOT NULL REFERENCES resistance_genes(gene_id)      ON DELETE RESTRICT,
    detection_method VARCHAR(100) NULL,
    detected_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (record_id, gene_id)          -- Prevent duplicate gene linkages per isolate
);

CREATE INDEX IF NOT EXISTS idx_irg_record_id ON isolate_resistance_genes (record_id);
CREATE INDEX IF NOT EXISTS idx_irg_gene_id   ON isolate_resistance_genes (gene_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- SUPPORTING TABLES: alerts, guidance_briefs
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    amr_isolate_record_id UUID NOT NULL REFERENCES amr_isolate_records(record_id) ON DELETE CASCADE,
    detection_timestamp   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    anomaly_score         NUMERIC NOT NULL,
    hotspot_magnitude     NUMERIC NOT NULL,
    feature_importance    JSONB NULL,
    status                VARCHAR(50) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'NOTIFIED'))
);

CREATE INDEX IF NOT EXISTS idx_alerts_record_id  ON alerts (amr_isolate_record_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status     ON alerts (status);
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp  ON alerts (detection_timestamp DESC);


CREATE TABLE IF NOT EXISTS guidance_briefs (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id              UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    generation_timestamp  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    role_target           VARCHAR(50) NOT NULL,
    content_markdown      TEXT NOT NULL,
    status                VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED'))
);

CREATE INDEX IF NOT EXISTS idx_guidance_alert_id ON guidance_briefs (alert_id);
CREATE INDEX IF NOT EXISTS idx_guidance_role     ON guidance_briefs (role_target);


-- ─────────────────────────────────────────────────────────────────────────────
-- PATHOGEN NORMALIZATION TRIGGER
-- PL/pgSQL pre-commit trigger — tg_normalize_pathogen_name
-- Normalizes common shorthand pathogen names to their full taxonomic forms
-- before storage. Applied BEFORE INSERT OR UPDATE on amr_isolate_records.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION tg_normalize_pathogen_name()
RETURNS TRIGGER AS $$
BEGIN
    -- Enterobacteriaceae
    IF NEW.pathogen_name ILIKE '%E. coli%' OR NEW.pathogen_name ILIKE '%E coli%' THEN
        NEW.pathogen_name := 'Escherichia coli';

    -- Staphylococci
    ELSIF NEW.pathogen_name ILIKE '%S. aureus%' OR NEW.pathogen_name ILIKE '%S aureus%' THEN
        NEW.pathogen_name := 'Staphylococcus aureus';

    -- Klebsiella
    ELSIF NEW.pathogen_name ILIKE '%K. pneumoniae%' OR NEW.pathogen_name ILIKE '%K pneumoniae%' THEN
        NEW.pathogen_name := 'Klebsiella pneumoniae';

    -- Acinetobacter
    ELSIF NEW.pathogen_name ILIKE '%A. baumannii%' OR NEW.pathogen_name ILIKE '%A baumannii%' THEN
        NEW.pathogen_name := 'Acinetobacter baumannii';

    -- Pseudomonas
    ELSIF NEW.pathogen_name ILIKE '%P. aeruginosa%' OR NEW.pathogen_name ILIKE '%P aeruginosa%' THEN
        NEW.pathogen_name := 'Pseudomonas aeruginosa';

    -- Salmonella (common poultry/animal pathogen for Kenya datasets)
    ELSIF NEW.pathogen_name ILIKE '%S. typhi%' OR NEW.pathogen_name ILIKE '%S typhi%' THEN
        NEW.pathogen_name := 'Salmonella typhi';
    ELSIF NEW.pathogen_name ILIKE '%S. enterica%' OR NEW.pathogen_name ILIKE '%S enterica%' THEN
        NEW.pathogen_name := 'Salmonella enterica';

    -- Streptococci
    ELSIF NEW.pathogen_name ILIKE '%S. pneumoniae%' OR NEW.pathogen_name ILIKE '%S pneumoniae%' THEN
        NEW.pathogen_name := 'Streptococcus pneumoniae';

    -- Enterococcus
    ELSIF NEW.pathogen_name ILIKE '%E. faecium%' OR NEW.pathogen_name ILIKE '%E faecium%' THEN
        NEW.pathogen_name := 'Enterococcus faecium';
    ELSIF NEW.pathogen_name ILIKE '%E. faecalis%' OR NEW.pathogen_name ILIKE '%E faecalis%' THEN
        NEW.pathogen_name := 'Enterococcus faecalis';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_normalize_pathogen_name
BEFORE INSERT OR UPDATE ON amr_isolate_records
FOR EACH ROW
EXECUTE FUNCTION tg_normalize_pathogen_name();


-- ─────────────────────────────────────────────────────────────────────────────
-- LEGACY COMPATIBILITY VIEW
-- Provides backward-compatible column name aliases for v1.2 ORM consumers
-- while the ORM migration is in progress.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW amr_isolate_records_v12_compat AS
SELECT
    record_id           AS id,
    pathogen_name,
    antibiotic_name     AS antimicrobial_agent,
    sir_result          AS result_value,
    county,
    sub_county,
    sector,
    sample_collection_date,
    data_quality_score,
    missing_fields,
    ncbi_taxonomy_id    AS ncbi_tax_id,
    sequencing_platform,
    assembly_id,
    accession_number,
    qc_status,
    patient_sex,
    patient_age_years,
    admission_type,
    clinical_indication,
    animal_species,
    production_system,
    infarm_compliant,
    animuse_compliant,
    glass_eligible,
    woah_animal_aware_class,
    antimicrobial_residue_ppm,
    is_synthetic,
    latitude,
    longitude,
    classification,
    resistance_rate,
    resistance_percent,
    sample_size,
    specimen_type,
    hospitalised,
    outcome,
    reported_by,
    submission_type
FROM amr_isolate_records;

-- ── Schema migration complete — v1.3 ─────────────────────────────────────────
