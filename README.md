# AMR-Nexus - Full-Stack AMR Surveillance Platform

**Production-grade · Offline-first · AI-powered · One Health**

[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-ML-orange.svg)](https://xgboost.ai)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](#license)

---

## Project Overview

AMR-Nexus is a full-stack, AI-powered platform for antimicrobial resistance (AMR) surveillance and prediction.

It combines:

- XGBoost for MDR prediction
- Isolation Forest for anomaly detection
- SHAP for explainability
- Real-time alerts via WebSocket and SMS
- Offline-first PWA with IndexedDB drafts
- Claude-powered stewardship guidance
- Interactive county heatmap with 47 Kenyan counties
- Role-based dashboards (National / County)
- Compare predictions side-by-side
- Bulk CSV/JSON import with validation

Designed for:

- Epidemiologists
- Laboratory technicians
- Veterinary officers
- Public health agencies
- National AMR coordinators

---

## Key Differentiators

| Feature | Description |
|---|---|
| ML Interpretability | SHAP values explain every prediction in plain language |
| Offline-first | IndexedDB drafts + service worker caching; sync when online |
| Real-time Alerts | WebSocket pushes anomalies + SMS notifications (Africa's Talking) |
| Role-based Views | National vs County dashboards with filtered data |
| Decision Support | Claude API generates role-specific stewardship recommendations |
| Professional UX | Dark mode, keyboard shortcuts, glass-morphic design |
| Production-ready | Dockerised, CI/CD friendly, scalable |
| Compare Predictions | Side-by-side comparison of records or uploaded CSV/JSON |
| Auto-forecast | Linear regression forecasting for MDR trends |
| Data Quality | Completeness metrics and validation |

---

## Architecture

```
+----------------------------------------------------------------+
|                        Browser / PWA                            |
|   React 19 | Vite | Zustand | Recharts | Socket.IO Client       |
+---------------------------+--------------------------------------+
                            |
                     HTTP / WebSocket
                            |
                            v
+----------------------------------------------------------------+
|                  FastAPI Backend (Uvicorn)                      |
|                                                                  |
|  - REST APIs (30+ endpoints)                                    |
|  - Socket.IO server (real-time alerts)                          |
|  - Background tasks (email/SMS reports)                         |
|  - SQLAlchemy ORM (PostgreSQL / SQLite)                         |
+---------------+--------------------------------+----------------+
                |                                 |
                v                                 v
+---------------------------+       +---------------------------+
|         ML Models          |       |        PostgreSQL          |
|  - XGBoost                 |       |  - Predictions              |
|  - Isolation Forest        |       |  - Alerts                   |
|  - SHAP Explainer          |       |  - Comments                 |
|  - Prophet (forecast)      |       |  - Risk Scores               |
|  - Linear Regression       |       |  - User Templates            |
+---------------------------+       +---------------------------+
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite, Tailwind CSS |
| State Management | Zustand |
| Forms | React Hook Form + Zod |
| Charts | Recharts |
| Backend | FastAPI, Uvicorn, SQLAlchemy |
| Authentication | JWT-ready (python-jose) |
| ML & Forecasting | XGBoost, SHAP, Isolation Forest, Prophet, LinearRegression |
| Data Processing | Pandas, NumPy |
| Database | PostgreSQL / SQLite |
| Real-Time | Socket.IO |
| SMS | Africa's Talking |
| LLM Guidance | Claude API (Anthropic) |
| PDF Generation | reportlab, jsPDF (frontend) |
| Offline Storage | IndexedDB (localStorage fallback) |
| Infrastructure | Docker + Docker Compose |

---

## Quick Start (Local Development)

### Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL (optional — SQLite works out of the box)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/amr-nexus.git
cd amr-nexus
```

### 2. Backend Setup

```bash
cd backend/amr_nexus_ml
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file:

```ini
DATABASE_URL=sqlite:///./amr.db
MODEL_DIR=./models
```

Place trained ML models (`*.pkl`) in `models/`.

Create database tables:

```bash
python -c "from src.db.session import engine; from src.db.models import Base; Base.metadata.create_all(bind=engine)"
```

Start backend:

```bash
python -m src.main --reload
```

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

### 3. Frontend Setup

```bash
cd ../../Frotend
npm install
```

Create `.env`:

```ini
VITE_API_URL=http://localhost:8000
```

Start frontend:

```bash
npm run dev
```

Frontend: http://localhost:5173

### 4. (Optional) Offline PWA Testing

```bash
npm run build
npx serve dist -s
```

---

## Project Structure (Key Files)

```
amr-nexus/
├── backend/
│   └── amr_nexus_ml/
│       ├── src/
│       │   ├── api/
│       │   │   ├── routers/           # All route handlers
│       │   │   │   ├── analytics_router.py
│       │   │   │   ├── alerts_router.py
│       │   │   │   ├── ews_router.py
│       │   │   │   ├── user_router.py
│       │   │   │   └── ...
│       │   │   ├── deps.py
│       │   │   └── app.py             # FastAPI app
│       │   ├── core/
│       │   │   ├── config.py
│       │   │   └── ml.py              # ML model loading
│       │   ├── db/
│       │   │   ├── models.py          # SQLAlchemy models
│       │   │   └── session.py
│       │   ├── services/
│       │   │   ├── prediction_service.py
│       │   │   ├── forecast_utils.py  # Linear regression forecast
│       │   │   └── ...
│       │   ├── utils/
│       │   │   └── logger.py
│       │   └── main.py                # ASGI entry
│       ├── models/                    # .pkl files
│       └── requirements.txt
├── frontend/
│   └── Frotend/
│       ├── src/
│       │   ├── api/
│       │   │   └── client.js
│       │   ├── components/
│       │   │   ├── predictions/
│       │   │   │   ├── PredictionForm.jsx
│       │   │   │   └── ResultCard.jsx
│       │   │   ├── alerts/
│       │   │   ├── analytics/
│       │   │   ├── DraftsManager.jsx  # Offline drafts UI
│       │   │   └── ...
│       │   ├── hooks/
│       │   │   ├── useOfflineDrafts.js
│       │   │   └── ...
│       │   ├── pages/
│       │   │   ├── Compare.jsx        # Side-by-side comparison
│       │   │   ├── Dashboard.jsx
│       │   │   ├── Analytics.jsx
│       │   │   ├── Predictions.jsx
│       │   │   └── Alerts.jsx
│       │   ├── utils/
│       │   │   ├── offlineStorage.js  # IndexedDB helpers
│       │   │   └── constants.js
│       │   └── main.jsx
│       ├── public/
│       │   ├── ke_counties.geojson    # Kenyan county boundaries
│       │   └── sw.js                  # Service worker
│       ├── tailwind.config.js
│       └── package.json
└── docker-compose.yml
```

---

## Core API Endpoints (selected)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/predict` | MDR prediction + SHAP + store |
| GET | `/predictions` | Paginated history |
| DELETE | `/predictions/{record_id}` | Delete a record |
| PATCH | `/predictions/{record_id}/note` | Update note |
| GET | `/analytics/summary` | Aggregated metrics |
| GET | `/analytics/mdr_trend` | Monthly trend |
| GET | `/analytics/by_pathogen` | Pathogen resistance |
| GET | `/analytics/by_sector` | MDR % by sector |
| GET | `/analytics/top_counties` | Highest MDR counties |
| GET | `/analytics/county_mdr` | Per-county rates (heatmap) |
| GET | `/analytics/pathogen_trend` | Pathogen-specific trend |
| GET | `/analytics/risk_scores` | Risk scores per county/pathogen |
| GET | `/ews/forecast` | County-level MDR forecast (6 months) |
| GET | `/alerts` | Active alerts |
| GET | `/alerts/count` | Unacknowledged count |
| PATCH | `/alerts/{id}/read` | Acknowledge alert |
| POST | `/records/bulk` | Bulk CSV/JSON import |
| GET | `/search?q=` | Global search |
| POST | `/guidance` | Claude-generated guidance |
| GET | `/metadata/options` | Dynamic form options |
| GET | `/templates` | User-saved form templates |
| POST | `/templates` | Save form template |
| DELETE | `/templates/{id}` | Delete template |
| GET | `/export/predictions` | Full CSV export |
| POST | `/reports/email` | Schedule email report |

---

## Frontend Features (page by page)

| Route | Features |
|---|---|
| `/` | Dashboard — metrics, trend, anomaly feed, county heatmap, system health |
| `/predict` | Offline drafts, speech-to-text, barcode, SHAP explanation, stewardship recommendation |
| `/compare` | Side-by-side comparison of predictions or uploaded CSV/JSON |
| `/analytics` | Interactive charts, date filters, forecast overlay, heatmap, pathogen-antibiotic matrix |
| `/history` | Paginated table, bulk actions, column customisation, compare modal |
| `/alerts` | Real-time anomalies, acknowledge, filter, export CSV, stats summary |
| `/reports` | Generate custom reports, CSV/PDF export, email scheduling |
| `/settings` | Profile, notifications, API keys, backup/restore, offline sync |
| `/pathogen-explorer` | Drill-down by pathogen: resistance per antibiotic, trend, heatmap |
| `/bulk-import` | Upload Excel/CSV with predictions |
| `/data-quality` | Completeness metrics |

---

## Offline-First Architecture

AMR-Nexus includes a robust offline-first experience:

**IndexedDB Storage**
- Prediction drafts are saved locally when offline
- Automatic sync when connection is restored
- Bulk sync all drafts with one click

**Components**
- `useOfflineDrafts` — Custom hook for draft management
- `DraftsManager` — UI component showing pending drafts
- `offlineStorage.js` — IndexedDB wrapper with CRUD operations

**Workflow**
1. User fills prediction form (online or offline)
2. Drafts are saved to IndexedDB every 30 seconds
3. "Sync All" button sends all drafts to server
4. Successful sync removes drafts from local storage

---

## Real-Time Alerts

- WebSocket connection via Socket.IO
- Anomaly detection triggers instant alerts
- Dashboard notifications appear in real-time
- SMS notifications via Africa's Talking
- Alerts can be acknowledged or dismissed

---

## Forecasting Engine

The `/ews/forecast` endpoint uses linear regression on historical MDR data to predict the next 6 months of MDR rates:

1. Fetches monthly MDR rates for the past 24 months
2. Fits a linear trend line
3. Projects forward 6 months
4. Returns a JSON array of predicted rates

**Example Response**

```json
[
  {"predicted_mdr_rate": 62.34},
  {"predicted_mdr_rate": 64.12},
  {"predicted_mdr_rate": 65.78},
  {"predicted_mdr_rate": 67.01},
  {"predicted_mdr_rate": 68.23},
  {"predicted_mdr_rate": 69.45}
]
```

---

## Integration Testing

**Health check**

```bash
curl http://localhost:8000/health
```

**Browser console test**

```js
fetch('http://localhost:8000/predictions')
  .then(r => r.json())
  .then(console.log)
```

**Submit a test prediction**

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "sector": "ANIMAL",
    "sub_sector": "Poultry-Broiler",
    "pathogen_code": "eco",
    "specimen_type": "Cloacal swab",
    "county": "Nairobi",
    "antibiotic_class": "Fluoroquinolone",
    "test_method": "Disk diffusion",
    "sample_month": 6
  }'
```

**Test forecast endpoint**

```bash
curl http://localhost:8000/ews/forecast?county=Nairobi
```

**Test all endpoints (PowerShell)**

```powershell
.\test-all.ps1   # see project root for the script
```

---

## Docker Deployment

**docker-compose.yml**

```yaml
version: '3'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: amr_db
      POSTGRES_USER: amr_user
      POSTGRES_PASSWORD: secret
    volumes:
      - pgdata:/var/lib/postgresql/data
  backend:
    build: ./backend/amr_nexus_ml
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://amr_user:secret@db:5432/amr_db
  frontend:
    build: ./frontend/Frotend
    ports:
      - "80:80"
volumes:
  pgdata:
```

**Build and run**

```bash
docker-compose up -d
```

---

## Environment Variables

**Backend `.env`**

```ini
DATABASE_URL=postgresql://user:pass@localhost/amr_db
MODEL_DIR=./models
AT_USERNAME=sandbox
AT_API_KEY=your_africastalking_key
AT_SENDER_ID=AMRNexus
CLAUDE_API_KEY=your_claude_key
ENABLE_SMS=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=reports@amrnexus.org
SMTP_PASS=******
```

**Frontend `.env`**

```ini
VITE_API_URL=http://localhost:8000
```

---

## License

Proprietary — AMR-Nexus One Health Project

All rights reserved. For internal research and public health use only.

---

## Contributors

| Role | Responsibility |
|---|---|
| Senior Developer | Full-stack architecture, DevOps, integration |
| ML Engineer | Model training, SHAP, Prophet, risk scoring |
| Frontend Developer | UI/UX, PWA, offline sync, charts |

---

## Current Status (July 2026)

- ✅ MVP ready for July 14, 2026 demonstration
- ✅ Synthetic data backbone with 2444+ records, 45+ counties
- ✅ AI Early Warning Engine: trend analysis, anomaly detection, risk scores, heatmap, SHAP
- ✅ Decision-Support Layer: Claude-powered guidance, role-based views
- ✅ Real-time alerts (WebSocket + SMS sandbox)
- ✅ Offline-capable PWA with IndexedDB drafts
- ✅ Full reporting and export
- ✅ Compare predictions side-by-side
- ✅ County-level forecasting
- ✅ Bulk CSV/JSON import
- ✅ User templates for prediction forms

---

## Known Issues & Roadmap

**Known Issues**
- React key warning in pathogen charts (fixed in next patch)
- GeoJSON fallback for county map (local file recommended)

**Roadmap (Q3 2026)**
- Advanced ARIMA forecasting
- Multi-drug resistance patterns
- Enhanced role-based access control
- Mobile app (React Native)
- Integration with national health systems
- Real-time data streaming from labs

---

## Contact

For technical support or collaboration:

- **Email:** team@amrnexus.org
- **Repository:** internal Git URL

Built for antimicrobial stewardship and One Health surveillance.
Last updated: 2026-07-04
