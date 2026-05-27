-- database/schema_v1.1.sql
-- Migration: Add NCBI Taxonomy and Sequencing Metadata, plus Pathogen Normalization Trigger

-- 1. Extend the core amr_records table with new genomic metadata fields
ALTER TABLE amr_records
ADD COLUMN ncbi_tax_id INT NULL,
ADD COLUMN sequencing_platform VARCHAR(100) NULL,
ADD COLUMN assembly_id VARCHAR(100) NULL,
ADD COLUMN accession_number VARCHAR(100) NULL,
ADD COLUMN qc_status VARCHAR(50) NULL;

-- 2. Implement trigger routine to ensure pathogen_name is auto-normalized into standard formats
CREATE OR REPLACE FUNCTION normalize_pathogen_name()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.pathogen_name ILIKE '%E. coli%' THEN
        NEW.pathogen_name := 'Escherichia coli';
    ELSIF NEW.pathogen_name ILIKE '%S. aureus%' THEN
        NEW.pathogen_name := 'Staphylococcus aureus';
    ELSIF NEW.pathogen_name ILIKE '%K. pneumoniae%' THEN
        NEW.pathogen_name := 'Klebsiella pneumoniae';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_normalize_pathogen_name
BEFORE INSERT OR UPDATE ON amr_records
FOR EACH ROW
EXECUTE FUNCTION normalize_pathogen_name();

-- 3. Add a high-performance BTREE index on (ncbi_tax_id, pathogen_name)
-- Note: Assuming pathogen_name instead of pathogen_code based on the actual schema
CREATE INDEX idx_amr_records_ncbi_tax_id_pathogen_name 
ON amr_records USING btree(ncbi_tax_id, pathogen_name);
