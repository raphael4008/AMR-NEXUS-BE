# AMR-Nexus Backend Tasks

For architectural details, team boundaries, and interconnectivity, please see `README.md`.

## 🟢 Raph's Zone (Data Backbone & Security)
**Completed**:
- `[x]` Update `database/schema_v1.1.sql` with new genomic metadata.
- `[x]` Implement `pathogen_name` normalization database trigger.
- `[x]` Update Pydantic schemas in `backend/src/schemas/backbone.py` with `@field_validator`.
- `[x]` Fix `schema_v1.2.sql`: add `status` column to `alerts` + `guidance_briefs`, add `genomic_signals` table DDL.
- `[x]` Fix `security.py`: OAuth2 `tokenUrl` now matches actual `/api/v1/token` route (was `/api/v1/auth/token`).

**Pending**:
- `[ ]` Apply `schema_v1.2.sql` migration script into the TimescaleDB production instance.
- `[ ]` Add `latitude`, `longitude`, `specimen_type`, `resistance_rate`, `resistance_percent`, `classification`, `sample_size`, `hospitalised`, `outcome`, `reported_by` columns to ORM + DDL (10 dataset fields currently unmapped).

## 🔵 Naomi's Zone (API Core, Telemetry & Integrations)
**Completed**:
- `[x]` New metadata fields mapped inside `src/models/entities.py`.
- `[x]` Background workers verified safe with new genomic markers.
- `[x]` Telemetry and guidance alerts exposed to frontend via JSON endpoints.
- `[x]` Fix `anomaly_detector.py`: replaced `records[idx]` (DataFrame index) with `enumerate()` — critical wrong-record bug.
- `[x]` Fix `anomaly_detector.py`: single batch commit replaces per-alert commits.
- `[x]` Fix `anomaly_detector.py`: null-guard on `data_quality_score` before `float()` cast.
- `[x]` Fix `anomaly_detector.py`: accepts both `'R'` and `'Resistant'` result values.
- `[x]` Fix `cleaner.py`: SIR normalization added (maps `Resistant/Susceptible/Intermediate` → `R/S/I`).
- `[x]` Fix `cleaner.py`: pathogen normalization now case-insensitive (covers `e coli`, `E. Coli`, etc.).
- `[x]` Fix `api/intelligence.py`: N+1 query replaced with `joinedload` (10 queries → 1).

**Pending**:
- `[ ]` Wire Pydantic `AMRRecordCreate` validators into ingest pipeline (currently bypassed by DataCleaner).
- `[ ]` Replace hardcoded lat/lon in heatmap endpoint with real coordinates from ORM once fields are added.
- `[ ]` Add structured failure logging (replace `print()` in LLMAdvisoryEngine with DB error record).
- `[ ]` Parameterize LLM role generation — only generate relevant role's brief, not both.
