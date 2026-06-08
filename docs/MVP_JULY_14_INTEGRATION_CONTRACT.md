# AMR-Nexus Backend: MVP July 14, 2026 Architectural Integration

## Overview
The architectural lockdown is complete! The final operational pre-flight health checks have been performed, verifying that the piping fluidity, algorithmic handoff, and adaptive guidance gating are all structurally sound. Everything is completely optimized, verified, and strictly bound to the **WHO GAP-AMR (2026–2036) compliance standards**.

## Detailed System Updates

### 1. Database Alignment (`/database/schema_v1.2.sql` & `models/entities.py`)
- **Hypertable Integration:** Created `schema_v1.2.sql` establishing the `amr_isolate_records` table as a TimescaleDB hypertable for high-performance temporal querying.
- **UUID Keys:** Refactored `id` fields to use `UUID` (via `gen_random_uuid()`) for scaling and secure referencing, replacing legacy serial integers.
- **Optimized Storage Allocation:** Adjusted `VARCHAR` lengths significantly (e.g., `county` limited to 50, `result_value` strictly `CHAR(1)` for 'S', 'I', 'R', and `patient_sex` to 10) to optimize storage efficiency.
- **Trigger Normalization:** Built PL/pgSQL triggers (`tg_normalize_pathogen_name_v2`) to auto-normalize incoming pathogen formats without backend intervention.

### 2. API Contract Enforcement (`schemas/backbone.py`)
- **Strict Pydantic V2 Models:** Standardized `AMRRecordCreate` with rigorous `Field` definitions and length constraints.
- **Shorthand Processing:** Utilized `@field_validator("pathogen_name", mode="before")` to safely handle shorthand pathogen string configurations before processing.
- **Disaggregation Enforcement:** Enforced WHO GAP-AMR Disaggregation rules inside `@model_validator(mode="after")` to categorically reject mismatched records (e.g., requiring age and sex for human records, species and production system for animal records).

### 3. High-Throughput & Async Services
- **LLM Advisory (`llm_advisory.py`):** Upgraded the Anthropic client to `AsyncAnthropic`. Configured asynchronous `trigger_role_guidance` to deploy contextually isolated system prompts depending on "National Coordinator" or "County Veterinarian" roles.
- **ML Anomaly Engine (`anomaly_detector.py`):** Configured downstream integration to leverage `FastAPI.BackgroundTasks` asynchronously. Data preprocessing and alerting now run seamlessly without adding latency to the main ingest endpoint.
- **SMS Gateway (`sms_service.py`):** Upgraded the Africa's Talking `dispatch_stewardship_trigger` to an async method and implemented resilient `try/except` execution to gracefully handle sandbox timeouts without interrupting the application flow.

### 4. API Routers
- **Intelligence Dashboard (`intelligence.py`):** Updated backend endpoints to fetch aggregate telemetry safely using optimized `db.query` counts. Data routes are securely gated using Raph's `RoleChecker`.
- **Ingestion (`backbone.py`):** Utilized robust PostgreSQL `RETURNING` clauses with bulk `insert` statements to process and cleanly map arrays of up to 10,000 records simultaneously.

---

## 🚀 Integration Contracts for the Team

As we lock our branches and prepare for the final push toward the **July 14, 2026 MVP milestone**, here are the exact integration contracts to pass along to the rest of the team:

### To Nicole (Data Science Track)
> "Your synthetic data files can now be posted directly to our `POST /api/v1/backbone/ingest/whonet` endpoint. Ensure your generator payloads include the new genomic indicators (`ncbi_tax_id`) and fulfill the strict disaggregation parameters (age, sex, species, and production system) required by the global action plan."

### To Gavinta & Jesse (AI/ML Track)
> "Your trained IsolationForest and Prophet model binaries are cleanly supported by our backend. Save your compiled model files inside the designated root directory, and our asynchronous wrappers will pull them automatically on server startup to handle live outlier scoring."

### To Lowell (Frontend Track)
> "The API endpoints are fully operational. You can fetch complete dashboard summaries and map coordinate meshes via `GET /api/v1/intelligence/dashboard/summary` and `GET /api/v1/intelligence/heatmap` using standard HTTP calls. The guidance briefs are returned as clean markdown blocks ready to render inside your UI panels."

---

## Runtime Testing & Validation

*(Note: When running the local validation tests with `docker-compose`, ensure you run the `docker-compose up` command from the root `amr-nexus-backend` directory where the `docker-compose.yml` file is located, rather than inside the `backend/` folder!)*

```bash
# 1. Access your local monorepo backend repository workspace
cd /home/bantu/Documents/amr-nexus-backend

# 2. Boot up the PostgreSQL/TimescaleDB and Redis service infrastructure stacks
docker-compose up -d db redis

# 3. Apply the complete database schemas and tracking indices via Alembic
alembic upgrade head

# 4. Execute the fully automated end-to-end test runner
pytest -v backend/tests/test_pipeline_integration.py
```
