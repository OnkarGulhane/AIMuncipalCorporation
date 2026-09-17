# 🏛️ AI Municipal Corporation — Case & Grievance Management Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flutter](https://img.shields.io/badge/Flutter-Cross--Platform-02569B?style=flat&logo=flutter&logoColor=white)](https://flutter.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An **AI-Powered, Multi-Role Municipal Complaint Redressal & Civic Case Management Platform** built for Municipal Corporations, Ward Offices, and Citizens. 

It streamlines the entire civic lifecycle: **Citizen Complaint → AI Triage & Duplicate Clustering → Field Squad Assignment → On-Site Investigation → SLA & Risk Tracking → Escalations → Citizen Resolution Confirmation → Management Analytics**.

---

## 🌟 Key Architecture & Capabilities

- 🤖 **AI Copilot & Triage Engine**: Auto-classifies complaints, detects vicinity duplicates, flags missing information, and crafts contextual citizen response drafts with human-in-the-loop overrides.
- ⏱️ **Dynamic SLA & Multi-Factor Risk Engine**: Computes SLA deadlines scaled by severity and priority, alerts at 75% breach thresholds, and calculates operational risk scores.
- ⏰ **In-Process Background Automation**: Powered by APScheduler for automatic periodic SLA breach escalations without heavy message queue overhead.
- 👥 **5-Tier Server-Side RBAC**: Strict privacy isolation between Citizens (Requesters), Field Operators, Team Leads, Ward Managers, and Chief Administrators.
- 💬 **Integrated Activity & Unified Timeline**: Citizen-Staff chat, private internal notes (strictly hidden from requesters), field task delegation, and on-site investigation logs.
- 📷 **Evidence & Attachment Storage**: Multipart file upload with MIME type enforcement, download streaming, and object storage support.
- 📊 **Ward Intelligence Dashboards**: Real-time KPI cards, SLA compliance metrics, ward heatmaps, and AI operational recommendations.
- 🛡️ **Immutable Audit Logging**: Automatic cryptographic-grade event capture for compliance and administrative oversight.

---

## 👥 5 Municipal Roles & Live Demo Credentials

The database includes pre-configured demo accounts for all 5 roles.

| Role | Email | Password | Description |
|---|---|---|---|
| 👤 **Citizen (Requester)** | `citizen@demo.city.gov` | `Password123` | File complaints, attach photos, track timeline, chat with staff, confirm/reject resolution. |
| 👷 **Field Operator** | `operator@demo.city.gov` | `Password123` | Claim assigned cases, request citizen info, log field findings, complete subtasks, propose resolutions. |
| 👩‍💼 **Team Lead** | `teamlead@demo.city.gov` | `Password123` | Monitor squad workload, delegate tasks, approve emergency resources, resolve escalations. |
| 👨‍💼 **Ward Manager** | `manager@demo.city.gov` | `Password123` | City & ward analytics, SLA compliance trends, department performance, AI risk alerts. |
| 👑 **Administrator** | `admin@demo.city.gov` | `Password123` | Manage departments, categories, teams, users, permissions, system stats, and audit logs. |

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Python 3.11+** installed
- **Git** installed
- *(Optional)* **Docker & Docker Compose**

### 2. Backend Setup (Local Virtualenv)

```powershell
# 1. Clone the repository
git clone https://github.com/OnkarGulhane/AIMuncipalCorporation.git
cd AIMuncipalCorporation/backend

# 2. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate   # On Linux/macOS: source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize Database & Seed Demo Data
python scripts/seed_demo_data.py

# 5. Start FastAPI Development Server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- 📖 **Interactive API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- 🩺 **Health Probe**: [http://localhost:8000/health](http://localhost:8000/health)
- 🚦 **Readiness Probe**: [http://localhost:8000/ready](http://localhost:8000/ready)

---

### 3. Docker Compose (One-Click Stack)

To run the complete stack (FastAPI + PostgreSQL 15) in containers:

```powershell
# From project root
docker-compose up --build -d
```

To run the automated database seeder inside the container:
```powershell
docker-compose exec api python scripts/seed_demo_data.py
```

---

### 4. Flutter Mobile & Web Application

The Flutter application code is located in [`mobile/`](mobile/) and supports **Android, iOS, Web, and Desktop**:

```powershell
cd mobile

# Run on Web (Chrome Browser)
flutter run -d chrome

# Run on Android Emulator or connected device
flutter run -d android

# Build production web bundle
flutter build web --release
```

---

## 🧪 Automated Testing Suite

The project includes an end-to-end automated test suite covering all 14 phases (RBAC, Case Lifecycle, AI Triage, SLAs, Escalations, Notifications, Dashboards, Audit, and Production Guards):

```powershell
# Run all backend tests
pytest backend/tests -v
```

---

## ☁️ Cloud Deployment (Render & Supabase)

### Deploy to Render.com
1. Fork or push this repository to GitHub.
2. In Render Dashboard, click **New +** → **Blueprint**.
3. Select your repository. Render will automatically detect [`render.yaml`](render.yaml) and provision:
   - **FastAPI Web Service**: with auto-migrations on boot.
   - **Managed PostgreSQL Database**: connected via internal environment variables.

### Environment Configuration
Refer to [`.env.production.example`](backend/.env.production.example) for setting up Supabase Storage, SendGrid SMTP, and External AI API keys in production.

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
