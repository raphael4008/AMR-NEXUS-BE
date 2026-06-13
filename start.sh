#!/usr/bin/env bash
# start.sh — AMR-Nexus One Health Platform v2.1
# Run from the project root: ./start.sh [api|worker|frontend|all]
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$PROJECT_ROOT/venv"
BACKEND="$PROJECT_ROOT/backend"
FRONTEND="$PROJECT_ROOT/frontend"

# Activate venv
# shellcheck disable=SC1091
source "$VENV/bin/activate"

MODE="${1:-help}"

case "$MODE" in
  api)
    echo "🚀 Starting FastAPI server on :8080..."
    cd "$BACKEND" && uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
    ;;
  worker)
    echo "⚙️  Starting ARQ worker..."
    cd "$BACKEND" && arq src.workers.arq_worker.WorkerSettings
    ;;
  frontend)
    echo "🌐 Starting Vite dev server on :5173..."
    cd "$FRONTEND" && npm run dev
    ;;
  migrate)
    echo "🗄️  Running Alembic migrations..."
    cd "$PROJECT_ROOT" && PYTHONPATH=backend alembic upgrade head
    ;;
  seed)
    echo "🌱 Seeding default users..."
    cd "$BACKEND" && python -m src.utils.seed_users
    ;;
  db-up)
    echo "🐳 Starting DB + Redis containers..."
    cd "$PROJECT_ROOT" && docker compose up -d db redis
    ;;
  all)
    echo ""
    echo "Open 3 separate terminals and run:"
    echo "  Terminal 1 (API):      ./start.sh api"
    echo "  Terminal 2 (Worker):   ./start.sh worker"
    echo "  Terminal 3 (Frontend): ./start.sh frontend"
    echo ""
    echo "Or for first-time setup:"
    echo "  ./start.sh db-up      # Start PostgreSQL + Redis"
    echo "  ./start.sh migrate    # Run DB migrations"
    echo "  ./start.sh seed       # Create default users"
    echo "  ./start.sh api        # Terminal 1"
    echo "  ./start.sh worker     # Terminal 2"
    echo "  ./start.sh frontend   # Terminal 3"
    echo ""
    echo "Default login credentials:"
    echo "  admin     / AMRNexus2026!  (National Coordinator)"
    echo "  vet_coord / AMRNexus2026!  (County Veterinarian)"
    echo "  clinician / AMRNexus2026!  (County Clinician)"
    echo ""
    echo "API docs: http://localhost:8080/docs"
    echo "Frontend: http://localhost:5173"
    ;;
  help|*)
    echo "Usage: ./start.sh [api|worker|frontend|migrate|seed|db-up|all]"
    ;;
esac
