# 🌿 AMR-Nexus Backend & Database Track Milestone Task Matrix

[cite_start]**Target MVP Milestone**: July 14, 2026 [cite: 7, 246]  
[cite_start]**Track Owners**: Raph (Infrastructure & Security) & Naomi (API Core & Integrations) [cite: 141]  
**Compliance Standards**: WHO GLASS | FAO InFARM | WOAH ANIMUSE | [cite_start]WHO GAP-AMR 2026-2036 [cite: 235, 321]

---

## [cite_start]🟢 Component A: Data Ingestion & Backbone (Raph's Zone) [cite: 28, 141]
- [x] [cite_start]**DDL Initialization (`/database/schema_v1.2.sql`)** [cite: 252, 297]
  - [cite_start]Create `amr_isolate_records`, `alerts`, and `guidance_briefs` relational architecture[cite: 252].
  - [cite_start]Partition the fact table by `sample_collection_date` into a TimescaleDB Hypertable[cite: 255, 300].
  - [cite_start]Inject peer-requested metadata: `ncbi_tax_id`, `sequencing_platform`, `assembly_id`, `accession_number`, and `qc_status`[cite: 259, 261].
  - [cite_start]Inject global reporting flags: `infarm_compliant`, `animuse_compliant`, `glass_eligible`, and `woah_animal_aware_class`[cite: 271, 426, 431].
- [x] [cite_start]**Database Constraints & Normalization Triggers** [cite: 288, 290]
  - [cite_start]Implement a PL/pgSQL database trigger to intercept and normalize `pathogen_name` (e.g., "E. coli" -> "Escherichia coli")[cite: 290].
  - [cite_start]Enforce check constraints on `sir_result` ('S', 'I', 'R') and `submission_type` ('SYNTHETIC', 'REAL', 'VALIDATED')[cite: 257, 261, 290].
- [x] [cite_start]**Pydantic V2 Contract Gateways (`/backend/src/schemas/backbone.py`)** [cite: 236, 240]
  - [cite_start]Implement `@field_validator` for incoming pathogen name cleaning before data hits the database[cite: 290].
  - [cite_start]Enforce conditional parameters matching WHO GAP-AMR 2026-2036 disaggregation: human records require age/sex/indication; veterinary records require species/production system[cite: 263, 269, 430, 431].
- [x] [cite_start]**Secure Authentication Routing (`/backend/src/api/auth.py`)** [cite: 147]
  - Expose `POST /api/v1/auth/token` using FastAPI's `OAuth2PasswordRequestForm`.
  - [cite_start]Issue cryptographically signed JWT tokens embedding explicit `role` claims ("National Coordinator", "County Veterinarian")[cite: 147, 155].
- [x] [cite_start]**Vectorized Ingestion Engine (`/backend/src/services/ingestion/cleaner.py`)** [cite: 28, 145]
  - [cite_start]Build Pandas-driven cleaner to calculate `data_quality_score`[cite: 257, 268].
  - [cite_start]Impute non-critical parameters (`facility_type` -> "Unknown", `sub_county` -> county-level mode) and write audit logs into a `missing_fields` JSONB block[cite: 257, 265, 290].

---

## [cite_start]🔵 Component B & C: Analytics & Telemetry (Naomi's Zone) [cite: 46, 69, 141]
- [x] [cite_start]**Asynchronous Machine Learning Wrapper (`/backend/src/services/ml_engine/anomaly_detector.py`)** [cite: 46, 143]
  - [cite_start]Implement `AMRAnomalyEngine` to map database records into numerical matrices for model inputs[cite: 47, 245].
  - [cite_start]Execute predictive scoring via background tasks using FastAPI's `BackgroundTasks` to prevent thread blocking[cite: 148, 304].
  - [cite_start]Create deterministic feature weight mappings to simulate SHAP explainability variables for Demo Day[cite: 62, 64].
- [x] [cite_start]**Role-Gated Prompt Engineering Engine (`/backend/src/services/intelligence/llm_advisory.py`)** [cite: 93, 141]
  - [cite_start]Build `LLMAdvisoryEngine` to connect to the Anthropic Claude API[cite: 93].
  - [cite_start]Implement a dynamic knowledge router mapping separate system prompts for "National Coordinator" (macro policy briefs) and "County Veterinarian" (tactical prescribing alternatives and SOP checklists)[cite: 79].
- [x] [cite_start]**Last-Mile Outbound Notification Worker (`/backend/src/services/notifications/sms_service.py`)** [cite: 67, 141]
  - [cite_start]Integrate the official Africa's Talking SDK running against the developer sandbox environment[cite: 67].
  - [cite_start]Dispatch asynchronous alerts wrapped in try-except statements to handle sandbox timeouts gracefully[cite: 67].
- [x] [cite_start]**Dashboard Telemetry Routers (`/backend/src/api/intelligence.py`)** [cite: 146]
  - [cite_start]Expose `GET /api/v1/intelligence/dashboard/summary` for index summaries[cite: 79].
  - [cite_start]Expose `GET /api/v1/intelligence/heatmap` to stream coordinate locations to Leaflet web maps[cite: 59, 61, 304].
