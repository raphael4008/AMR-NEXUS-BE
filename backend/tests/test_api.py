"""
test_api.py — Integration tests for the FastAPI HTTP layer (Rev 2).

Coverage targets:
  ✓ GET  /health                              → 200 with version + service name
  ✓ POST /api/v1/token                        → 200 with access_token placeholder
  ✓ POST /api/v1/backbone/ingest/whonet       → 200 with processing summary
  ✓ POST /api/v1/backbone/ingest/whonet       → 400 for empty payload
  ✓ GET  /api/v1/intelligence/dashboard       → 200 with telemetry keys
  ✓ GET  /openapi.json                        → confirms route registration

Notes:
- Tests use TestClient (synchronous) wrapping the async FastAPI app.
- DB dependency is overridden by conftest.py's in-memory SQLite.
"""

# pyrefly: ignore [missing-import]
import pytest


# ── /health ───────────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_contains_status_healthy(self, client):
        resp = client.get("/health")
        assert resp.json()["status"] == "healthy"

    def test_health_contains_version(self, client):
        resp = client.get("/health")
        assert resp.json()["version"] == "2.0.0"

    def test_health_contains_service_name(self, client):
        from src.core.config import settings
        resp = client.get("/health")
        assert resp.json()["service"] == settings.PROJECT_NAME


# ── /api/v1/token ─────────────────────────────────────────────────────────────

class TestAuthEndpoint:
    def test_token_endpoint_returns_200(self, client):
        resp = client.post("/api/v1/token")
        assert resp.status_code == 200

    def test_token_response_has_access_token(self, client):
        resp = client.post("/api/v1/token")
        assert "access_token" in resp.json()

    def test_token_response_has_token_type(self, client):
        resp = client.post("/api/v1/token")
        assert resp.json()["token_type"] == "bearer"


# ── /api/v1/backbone/ingest/whonet ────────────────────────────────────────────

class TestIngestEndpoint:
    def test_valid_payload_returns_200(self, client, valid_payload):
        resp = client.post("/api/v1/backbone/ingest/whonet", json=valid_payload)
        assert resp.status_code == 200

    def test_valid_payload_returns_success_status(self, client, valid_payload):
        resp = client.post("/api/v1/backbone/ingest/whonet", json=valid_payload)
        assert resp.json()["status"] == "success"

    def test_processed_records_count_correct(self, client, valid_payload):
        resp = client.post("/api/v1/backbone/ingest/whonet", json=valid_payload)
        assert resp.json()["processed_records"] == len(valid_payload)

    def test_no_critical_failures_for_clean_data(self, client, valid_payload):
        resp = client.post("/api/v1/backbone/ingest/whonet", json=valid_payload)
        assert resp.json()["failed_critical"] == 0

    def test_dirty_payload_identifies_critical_failures(self, client, dirty_payload):
        resp = client.post("/api/v1/backbone/ingest/whonet", json=dirty_payload)
        assert resp.status_code == 200
        assert resp.json()["failed_critical"] == 1

    def test_dirty_payload_processes_valid_records(self, client, dirty_payload):
        """processed_records should equal valid rows."""
        resp = client.post("/api/v1/backbone/ingest/whonet", json=dirty_payload)
        assert resp.json()["processed_records"] == len(dirty_payload) - 1

    def test_empty_payload_returns_400(self, client):
        resp = client.post("/api/v1/backbone/ingest/whonet", json=[])
        assert resp.status_code == 400

    def test_empty_payload_error_message(self, client):
        resp = client.post("/api/v1/backbone/ingest/whonet", json=[])
        assert "Payload must not be empty" in resp.json()["detail"]

    def test_response_has_message_field(self, client, valid_payload):
        resp = client.post("/api/v1/backbone/ingest/whonet", json=valid_payload)
        assert "message" in resp.json()

    def test_single_record_payload(self, client):
        single = [{
            "sector": "human",
            "pathogen_name": "E. coli",
            "antimicrobial_agent": "Ciprofloxacin",
            "county": "Nairobi",
            "result_value": "Resistant",
            "facility_type": "Hospital",
        }]
        resp = client.post("/api/v1/backbone/ingest/whonet", json=single)
        assert resp.status_code == 200
        assert resp.json()["processed_records"] == 1


# ── /api/v1/intelligence/dashboard/summary ──────────────────────────────────────

class TestIntelligenceEndpoint:
    def test_dashboard_returns_200(self, client):
        token = client.post("/api/v1/token").json()["access_token"]
        resp = client.get("/api/v1/intelligence/dashboard/summary", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_dashboard_returns_json(self, client):
        token = client.post("/api/v1/token").json()["access_token"]
        resp = client.get("/api/v1/intelligence/dashboard/summary", headers={"Authorization": f"Bearer {token}"})
        assert resp.headers["content-type"].startswith("application/json")

    def test_dashboard_has_telemetry_keys(self, client):
        """Rev 2 dashboard returns total_records, alerts_30d, top_pathogen, etc."""
        token = client.post("/api/v1/token").json()["access_token"]
        resp = client.get("/api/v1/intelligence/dashboard/summary", headers={"Authorization": f"Bearer {token}"})
        data = resp.json()
        assert "total_alerts" in data
        assert "alerts_last_30_days" in data


# ── OpenAPI Schema ────────────────────────────────────────────────────────────

class TestOpenAPISchema:
    def test_openapi_endpoint_reachable(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200

    def test_openapi_has_backbone_path(self, client):
        schema = client.get("/openapi.json").json()
        assert "/api/v1/backbone/ingest/whonet" in schema["paths"]

    def test_openapi_has_intelligence_path(self, client):
        schema = client.get("/openapi.json").json()
        assert "/api/v1/intelligence/dashboard/summary" in schema["paths"]

