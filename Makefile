# AMR-Nexus Backend — Project Makefile
# Usage: make <target>

.PHONY: help venv-activate install db-up db-migrate db-seed \
        run-api run-worker run-frontend run-all docker-up docker-down

VENV := venv/bin/activate
BACKEND_DIR := backend

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Environment ────────────────────────────────────────────────────────────────

venv-activate:  ## Print the command to activate the virtual environment
	@echo "Run: source $(VENV)"

install:  ## Install Python dependencies
	. $(VENV) && pip install -r $(BACKEND_DIR)/requirements.txt

# ── Database ───────────────────────────────────────────────────────────────────

db-up:  ## Start PostgreSQL and Redis via Docker Compose
	docker compose up -d db redis

db-migrate:  ## Run Alembic migrations (upgrade head)
	. $(VENV) && PYTHONPATH=$(BACKEND_DIR) alembic upgrade head

db-seed:  ## Seed initial admin users into the database
	. $(VENV) && cd $(BACKEND_DIR) && python -m src.utils.seed_users

# ── Development Servers ────────────────────────────────────────────────────────

run-api:  ## Start FastAPI backend (uvicorn with hot reload on :8080)
	. $(VENV) && cd $(BACKEND_DIR) && uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload

run-worker:  ## Start ARQ background worker
	. $(VENV) && cd $(BACKEND_DIR) && arq src.workers.arq_worker.WorkerSettings

run-frontend:  ## Start the Next.js / Vite frontend dev server
	cd frontend && npm run dev

run-all:  ## Instructions to run all services in separate terminals
	@echo ""
	@echo "  Open 3 separate terminal windows and run:"
	@echo ""
	@echo "  Terminal 1 (API):      make run-api"
	@echo "  Terminal 2 (Worker):   make run-worker"
	@echo "  Terminal 3 (Frontend): make run-frontend"
	@echo ""

# ── Docker ─────────────────────────────────────────────────────────────────────

docker-up:  ## Build and start all services with Docker Compose
	docker compose up --build

docker-down:  ## Stop and remove all Docker Compose services
	docker compose down
