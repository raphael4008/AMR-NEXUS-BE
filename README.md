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
