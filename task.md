# AMR-Nexus: Monorepo Task & Architecture Guide

Welcome to the central monorepo for AMR-Nexus. This platform is an AI-powered early warning and decision-support architecture designed to break down traditional data silos by connecting and cleaning messy datasets across Kenya's human, animal, and environmental sectors.

Our target objective is the successful implementation and presentation of our Minimum Viable Product (MVP) by our July 14, 2026 project milestone.

## 1. Repository Structure & Sub-Systems
This project uses a unified Monorepo design to prevent overlapping conflicts:
- `/.github/workflows/` – Automated CI/CD pipeline configuration files handling deployments to Google Cloud Run.
- `/backend/` – Python/Node.js application programming interfaces (APIs), server settings, and core business logic.
- `/database/` – PostgreSQL/BigQuery schema definitions, structured `.sql` DDL scripts, and database migration configurations.
- `/docs/` – Domain literature, project requirements, and the official WHO/GLASS standard data dictionary frameworks.
- `/frontend/` – User interface component assets, management dashboards, and client-side web hosting applications.
- `/ml-ai/` – Machine learning models, data analytics pipelines, and automated antimicrobial stewardship scanning algorithms.

## 2. Git Branching Strategy & Workflow Rules
To maintain absolute stability, direct pushes to the `main` branch are strictly prohibited. All features must be integrated via Peer-Reviewed Pull Requests.
- **Pull Latest**: `git checkout main && git pull`
- **Branch Off**: Create a localized branch targeting your track (e.g., `backend/feature-api-name`, `frontend/feature-ui-component`, `ml-ai/feature-algorithm-name`, `database/feature-migration-name`).
- **Commit & Push**: Keep commits concise and isolated to your assigned folder track. Open a PR.
- **Automated Verification**: Do not merge if the automated security check is red.
- **Peer Review**: Requires at least 1 other developer to review and approve.
- **Privacy Requirement**: You must enable "Keep my email addresses private" and "Block command line pushes that expose my email" in GitHub Settings.

## 3. Team Boundaries: Backend & Database (Raph & Naomi)
The backend is strictly divided between Raph and Naomi to optimize concurrent development and prevent merge conflicts. Future improvements must adhere to these exact folder and file assignments.

### 🟢 Raph's Zone (Data Backbone & Security)
**Focus**: DB integrity, DDL updates, API routing, data ingestion pipelines, and authentication.
**Core Folders & Files:**
- `src/api/backbone.py` (Ingestion Endpoints)
- `src/api/auth.py` (Security & Login, JWT generation)
- `src/core/security.py` (Role-Based Access Control configuration)
- `src/services/ingestion/cleaner.py` (Data cleaning and validation logic)
- `src/schemas/backbone.py` (Pydantic validation schemas for incoming data)
- `/database/` directory (All SQL scripts and schema definitions)

**Current Tasks**:
- `[x]` Update `database/schema_v1.1.sql` with new genomic metadata (`ncbi_tax_id`, `sequencing_platform`, `assembly_id`, `accession_number`, `qc_status`).
- `[x]` Implement `pathogen_name` normalization database trigger.
- `[x]` Update Pydantic schemas in `backend/src/schemas/backbone.py` with `@field_validator`.
- `[/]` Apply the updated `schema_v1.1.sql` migration script into the TimescaleDB instance.

### 🔵 Naomi's Zone (API Core, Telemetry & Integrations)
**Focus**: Exposing data, downstream processing, dashboard telemetry APIs, and notifications.
**Core Folders & Files:**
- `src/api/intelligence.py` (Telemetry and dashboard data aggregation endpoints)
- `src/services/notifications/sms_service.py` (External notification integrations like Africa's Talking)
- `src/schemas/intelligence.py` (Frontend contract validation schemas)

**Current Tasks**:
- `[x]` Ensure the new metadata fields are mapped inside the base repository models (`src/models/entities.py`).
- `[ ]` Verify that downstream background workers do not break when processing records containing these extra metadata points.
- `[ ]` Expose telemetry updates and guidance alerts to the frontend via JSON endpoints.

### 🟡 Shared / Handoff Zones
**Focus**: Where Raph and Naomi's code interacts. Modifying these requires cross-team communication.
- `src/models/entities.py`: SQLAlchemy database schemas. Naomi just updated this with Raph's new columns.
- `src/main.py`: Main FastAPI app configuration and routing setups.
- `requirements.txt`: Python package dependencies.
- `tests/test_api.py`: Shared integration testing suite.

## 4. Improvements & Advancements Made
- **Pathogen Standardization**: Enforcing the official genus-species classification. Incoming raw abbreviations (e.g., *E. coli*) are auto-normalized into canonical formats (e.g., *Escherichia coli*) via Pydantic and PostgreSQL triggers.
- **NCBI Taxonomy IDs**: Added `ncbi_tax_id` to the database layer as a unique, non-aliased numeric identifier for molecular and algorithmic pipelines.
- **Forward-Compatible Genomic Tracking**: Injected sequencing metadata placeholders to support upcoming Module 2 features without altering the central fact table structure later.

## 5. System Interconnectivity (Post-Backend Phase)
Once Raph and Naomi complete the `/backend/` and `/database/` tracks, the architecture scales outwards:
1. **Connecting the Database**: The `/backend/` FastAPI application connects directly to the PostgreSQL/TimescaleDB tables for transaction execution and data fetching.
2. **Connecting the AI/ML Engine**: The models in `/ml-ai/` operate externally (via isolation forest/LLMs). They poll or stream new records from the DB, perform anomaly detection, and write results back to the `alerts` and `guidance` tables.
3. **Connecting the Frontend**: The web applications in `/frontend/` consume the `/backend/` telemetry APIs (Naomi's zone) using standard RESTful contracts to display real-time interactive mapping, anomaly charts, and operational alerts.
