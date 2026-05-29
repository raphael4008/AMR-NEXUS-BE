# AMR-Nexus Backend Tasks

For architectural details, team boundaries, and interconnectivity, please see `README.md`.

## 🟢 Raph's Zone (Data Backbone & Security)
**Current Tasks**:
- `[x]` Update `database/schema_v1.1.sql` with new genomic metadata (`ncbi_tax_id`, `sequencing_platform`, `assembly_id`, `accession_number`, `qc_status`).
- `[x]` Implement `pathogen_name` normalization database trigger.
- `[x]` Update Pydantic schemas in `backend/src/schemas/backbone.py` with `@field_validator`.
- `[/]` Apply the updated `schema_v1.1.sql` migration script into the TimescaleDB instance.

## 🔵 Naomi's Zone (API Core, Telemetry & Integrations)
**Current Tasks**:
- `[x]` Ensure the new metadata fields are mapped inside the base repository models (`src/models/entities.py`).
- `[x]` Verify that downstream background workers do not break when processing records containing these extra metadata points.
- `[x]` Expose telemetry updates and guidance alerts to the frontend via JSON endpoints.
