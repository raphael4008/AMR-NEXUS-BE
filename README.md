<<<<<<< HEAD
#  AMR-Nexus One Health

### AI-Powered AMR Early Warning, Risk Assessment & Decision-Support Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![React](https://img.shields.io/badge/React-18-blue)](https://react.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3-38bdf8)](https://tailwindcss.com)
[![Vite](https://img.shields.io/badge/Vite-5-646cff)](https://vitejs.dev)
[![MSW](https://img.shields.io/badge/MSW-2-orange)](https://mswjs.io)

> **July 14, 2026 – Functional Proof-of-Concept**
>
> This frontend demonstrates a complete detection-to-action workflow using high-fidelity synthetic data.
>
> **Not intended for live operational surveillance.**

---

##  Overview

AMR-Nexus One Health transforms fragmented antimicrobial resistance (AMR) data into actionable intelligence for policymakers, clinicians, veterinarians, and surveillance teams.

The platform combines:

* Interactive surveillance mapping
* AI-powered early warning
* Explainable AI (SHAP)
* Decision-support workflows
* Role-based guidance
* Notification simulations

into a unified One Health surveillance platform.

---

##  Key Features

###  Interactive Surveillance Heatmap

* County-level AMR burden visualization
* Dark and light CartoDB map tiles
* Interactive county drill-downs
* Geographic resistance monitoring

###  AI-Powered Early Warning

* Resistance anomaly detection
* Trend analysis
* Simulated risk scoring
* Emerging hotspot identification

###  SHAP Explainability

Every alert includes:

* Plain-language explanation
* Feature contribution analysis
* Confidence indicators
* Risk drivers

###  Alert Workflow

```text
Alert Detected
      ↓
AI Explanation
      ↓
Recommended Actions
      ↓
SMS Notification
```

###  Dual Audience Support

**National Coordinators**

* Policy recommendations
* National AMR overview
* Resource prioritization

**County Clinicians & Veterinarians**

* Clinical guidance
* Stewardship recommendations
* Localized interventions

###  Responsive Design

* Mobile-first design
* Tablet optimized
* Desktop dashboards
* Adaptive layouts

###  Light & Dark Themes

* Instant theme switching
* Design token architecture
* Theme-aware maps and charts

---

##  Architecture

```text
src/
├── api/
│   ├── client.js
│   └── endpoints.js
│
├── components/
│   ├── alerts/
│   ├── dashboard/
│   ├── demo/
│   ├── layout/
│   ├── map/
│   ├── trends/
│   └── ui/
│
├── hooks/
│
├── lib/
│
├── mocks/
│   ├── handlers.js
│   └── browser.js
│
├── pages/
│
├── App.jsx
├── main.jsx
└── index.css
```

---

##  Data Flow

```text
Frontend (React)
        │
        ▼
 Axios API Client
        │
        ▼
 React Query Cache
        │
        ▼
 Mock Service Worker
        │
        ▼
 Synthetic Data Engine
        │
        ▼
 Dashboards & Alerts
```

### Architecture Layers

1. **API Layer (`api/client.js`)**

   * Axios instance
   * Request interceptors
   * API endpoint management

2. **React Query**

   * Data caching
   * Loading states
   * Error handling
   * Refetching

3. **State Management**

   * React Context
   * Theme state
   * User role state
   * Local UI state

4. **Theming**

   * CSS variables
   * Light/Dark tokens
   * Global styling strategy

---

##  Technology Stack

| Layer         | Technology           |
| ------------- | -------------------- |
| Framework     | React 18             |
| Build Tool    | Vite 5               |
| Styling       | Tailwind CSS 3       |
| Icons         | Lucide React         |
| Routing       | React Router v6      |
| Data Fetching | TanStack React Query |
| Maps          | React Leaflet        |
| Charts        | Recharts             |
| HTTP Client   | Axios                |
| Mock Backend  | MSW                  |
| Linting       | ESLint               |

---

##  Getting Started

### Prerequisites

```bash
Node.js >= 18
npm >= 9
```

### Clone Repository

```bash
git clone https://github.com/lumierecore-clg/amr-nexus-frontend.git

cd amr-nexus-frontend
```

### Install Dependencies

```bash
npm install
```

---

##  Environment Variables

Create a `.env` file:

```env
VITE_API_BASE_URL=/api

VITE_ENABLE_MSW=true
```

### Environment Variable Reference

| Variable          | Description                |
| ----------------- | -------------------------- |
| VITE_API_BASE_URL | Backend API URL            |
| VITE_ENABLE_MSW   | Enable Mock Service Worker |

---

##  Development

Start the development server:

```bash
npm run dev
```

Application URL:

```text
http://localhost:5173
```

Features enabled:

* Dark mode by default
* Synthetic surveillance data
* Full mock API support
* Interactive dashboards

---

##  Production Build

Build production assets:

```bash
npm run build
```

Preview locally:

```bash
npm run preview
```

---

##  API Endpoints

### Dashboard APIs

| Method | Endpoint              | Description    |
| ------ | --------------------- | -------------- |
| GET    | `/api/summary`        | Dashboard KPIs |
| GET    | `/api/map/choropleth` | County GeoJSON |
| GET    | `/api/alerts`         | Active alerts  |
| GET    | `/api/trends`         | Trend analysis |

### Alert APIs

| Method | Endpoint                      |
| ------ | ----------------------------- |
| GET    | `/api/alerts/:id`             |
| GET    | `/api/alerts/:id/explanation` |
| GET    | `/api/alerts/:id/guidance`    |

### Workflow APIs

| Method | Endpoint       |
| ------ | -------------- |
| POST   | `/api/ingest`  |
| POST   | `/api/process` |

---

##  Theming

Design tokens are defined in:

```text
src/index.css
```

### Light Theme

| Property   | Value   |
| ---------- | ------- |
| Background | #F8FAFC |
| Cards      | #FFFFFF |
| Accent     | #0D9488 |

### Dark Theme

| Property   | Value   |
| ---------- | ------- |
| Background | #0A0E17 |
| Cards      | #1A1F2E |
| Accent     | #00F0FF |

Map tiles automatically switch between:

* CartoDB Light
* CartoDB Dark

---

##  Demo Journeys

### National AMR Coordinator

1. Open National Dashboard
2. View KPIs
3. Explore Heatmap
4. Open Alert
5. Review SHAP Explanation
6. Send SMS Notification

### County Veterinarian

1. Switch Role
2. Open County Dashboard
3. Review Poultry Trends
4. Analyze Local Alerts
5. View Veterinary Guidance

---

##  Responsive Design

### Mobile (< 640px)

* Sidebar overlay
* Single-column layout
* Touch-friendly controls

### Tablet (640px–1024px)

* Two-column KPI grids
* Enhanced navigation

### Desktop (>1024px)

* Full sidebar
* Four-column dashboard
* Maximum information density

---

## ✅ Mentor Feedback Implemented

* ✅ Stable county map rendering
* ✅ Reduced white space
* ✅ Improved chart readability
* ✅ Enhanced filters
* ✅ Four-step alert workflow
* ✅ SHAP contributor visualization
* ✅ Theme consistency
* ✅ Guidance action buttons
* ✅ Status indicator badges
* ✅ Refined spacing and alignment
* ✅ Complete MVP story flow

---

##  Contributing

Fork the repository:

```bash
git fork
```

Create a feature branch:

```bash
git checkout -b feature/amazing-feature
```

Commit changes:

```bash
git commit -m "Add amazing feature"
```

Push changes:

```bash
git push origin feature/amazing-feature
```

Create a Pull Request.

---

##  License

MIT License

```text
Copyright (c) 2026 LumiereCore CLG


```

---

## 📧 Contact

**Project:** AMR-Nexus One Health

**Project Lead:** 

**Email:** 
**Demo Date:** July 14, 2026

---

##  Vision

AMR-Nexus One Health aims to strengthen antimicrobial resistance surveillance through:

* Early detection
* Explainable AI
* One Health integration
* Evidence-based decision support
* Rapid response workflows

Together, these capabilities help transform AMR data into actionable public health intelligence.
=======
# 🌍 AMR-Nexus: Unifying Health Security Through One Health Intelligence

Welcome to the central monorepo for **AMR-Nexus**. This platform is an AI-powered early warning and decision-support architecture designed to break down traditional data silos by connecting and cleaning messy datasets across Kenya's human, animal, and environmental sectors. 

Our target objective is the successful implementation and presentation of our Minimum Viable Product (MVP) by our **July 14, 2026** project milestone.

---

## 📂 Repository Structure

This project uses a unified **Monorepo** design. All tracks work inside this single repository, using designated root folders to prevent overlapping conflicts:

* **`/.github/workflows/`** – Automated CI/CD pipeline configuration files handling seamless deployments to Google Cloud Run.
* **`/backend/`** – Python/Node.js application programming interfaces (APIs), server settings, and core business logic.
* **`/database/`** – PostgreSQL/BigQuery schema definitions, structured `.sql` DDL scripts, and database migration configurations.
* **`/docs/`** – Domain literature, project requirements, and the official WHO/GLASS standard data dictionary frameworks.
* **`/frontend/`** – User interface component assets, management dashboards, and client-side web hosting applications.
* **`/ml-ai/`** – Machine learning models, data analytics pipelines, and automated antimicrobial stewardship scanning algorithms.

---

## 🌿 Git Branching Strategy & Workflow

To maintain absolute stability on our core codebase, **direct pushes to the `main` branch are strictly prohibited by team policy.** All features must be integrated via Peer-Reviewed Pull Requests monitored by our automated security guard.

### 1. The Workflow Rules
1. **Pull Latest:** Before creating a branch, ensure your local environment is synchronized with production: `git checkout main && git pull`
2. **Branch Off:** Create a localized feature branch off `main` named according to your specific category team track (see conventions below).
3. **Commit Code:** Keep commits concise, clean, and isolated to your assigned folder track.
4. **Push & PR:** Push your feature branch to GitHub and open a **Pull Request (PR)** targeting `main`.
5. **Automated Verification:** An automated script will immediately run and flag the PR with a red warning check. 
6. **Peer Review:** At least **1 other developer** must review and officially **Approve** the PR. Once approved, the automated check will turn green, and only then are you authorized to safely merge your code. Do not merge if the automated check is red!


### 2. Track-Specific Naming Conventions-MUST COMPLY
When building a new feature, name your working branches using your specific category prefix:
* **Backend Track:** `backend/feature-api-name`
* **Frontend Track:** `frontend/feature-ui-component`
* **ML/AI Track:** `ml-ai/feature-algorithm-name`
* **Database Track:** `database/feature-migration-name`

---


## 🔒 Personal Privacy Requirement

Before executing your very first command-line push to this repository, you **must** secure your personal email privacy settings inside your GitHub profile:
1. Navigate to your personal GitHub **Settings** $\rightarrow$ **Emails**.
2. Check the box: **"Keep my email addresses private"**.
3. Check the box: **"Block command line pushes that expose my email"**.

---
>>>>>>> 53cc4291c72aaccb7f501b039baea2234fca8041
