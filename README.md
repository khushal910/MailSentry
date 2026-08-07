# MailSentry 🛡️

[![MailSentry CI Pipeline](https://github.com/khushal910/MailSentry/actions/workflows/ci.yml/badge.svg)](https://github.com/khushal910/MailSentry/actions/workflows/ci.yml)
[![MailSentry Production CD](https://github.com/khushal910/MailSentry/actions/workflows/deploy.yml/badge.svg)](https://github.com/khushal910/MailSentry/actions/workflows/deploy.yml)
[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Node.js Version](https://img.shields.io/badge/node-20.x-green.svg)](https://nodejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com/)
[![React + TypeScript](https://img.shields.io/badge/React-19.0-61DAFB.svg)](https://react.dev/)

> **Real-Time AI Email Classification, Microservice Architecture & Automated Threat Intelligence Platform**

MailSentry is an enterprise-grade email security, classification, and threat monitoring system powered by an independent Machine Learning microservice (`ml-service`), an asynchronous REST API backend (`backend`), and a modern React Web Application (`frontend`).

---

## 🏗️ System Architecture

```text
React Frontend (Vercel)
        │
        ▼
Backend API (Render :8000)
        │
        ├── Authentication & JWT
        ├── Email Management & OTP
        ├── Database (MongoDB Atlas)
        └── MLServiceClient (HTTP Client)
               │
               ▼
ML Microservice (Render :9000)
        ├── FastAPI Engine
        ├── URLFeatureExtractor & Preprocessing
        └── Production Model Artifacts (model.joblib, preprocessing.pkl, schema.yaml)
```

---

## 🔄 CI/CD Pipeline Architecture & Validation Flow

MailSentry enforces strict automated Quality & Security Gates. **Production deployments only trigger after all CI test suites pass.**

```text
Push / Pull Request (main)
        │
        ▼
  GitHub Actions CI (ci.yml)
        │
 ┌──────┼───────────────────┐
 │      │                   │
 ▼      ▼                   ▼
Frontend CI         Backend CI          ML-Service CI
- npm install       - Python 3.11 / uv  - Python 3.11 / uv
- tsc type check    - Ruff linting      - Preprocessing tests
- Vite build        - Pytest suite      - Feature extraction tests
                    - Startup probe     - API router tests
                                        - Schema & artifact load
 └──────┬───────────────────┘
        │
        ▼
  Cross-Service Integration Gate
  (Backend <-> ML Service Client)
        │
        ▼
  All Passed? ─── NO ───► Block Merge / Stop Deployment
        │
       YES
        │
        ▼
  Production Deployment (deploy.yml)
 ┌──────┴───────────────────┐
 │                          │
 ▼                          ▼
Deploy Backend             Deploy ML-Service
(Render Deploy Hook)       (Render Deploy Hook)
 │                          │
 └──────────┬───────────────┘
            │
            ▼
 Post-Deploy Health Verification
```

---

## 🧪 Local Microservice Setup & Testing

### 1. Launch All Microservices (Windows Launcher)
```cmd
run.bat
```

### 2. Manual Service Setup

#### A. ML Inference Microservice (:9000)
```bash
cd ml-service
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
Run ML tests:
```bash
python -m unittest discover -s tests
```

#### B. Backend API Server (:8000)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
Run Backend tests:
```bash
pytest tests
```

#### C. React Frontend (:5173)
```bash
cd frontend
npm install
npm run dev
```
Run Frontend type check & build validation:
```bash
npm run test
npm run build
```

---

## 🔒 GitHub Branch Protection Rules (Required Configuration)

To enforce that Pull Requests cannot be merged until all CI checks pass:

1. Open your GitHub Repository $\rightarrow$ **Settings** $\rightarrow$ **Branches**.
2. Under **Branch protection rules**, click **Add branch protection rule**.
3. Set **Branch name pattern** to `main`.
4. Enable the following settings:
   - ✅ **Require a pull request before merging**
   - ✅ **Require status checks to pass before merging**
   - ✅ **Require branches to be up to date before merging**
   - Search and select required status checks:
     * `Frontend CI (Types & Production Build)`
     * `Backend CI (Quality, Type Check & Tests)`
     * `ML Microservice CI (Artifacts, Engine & Endpoints)`
     * `Cross-Service Integration Gate`
5. Click **Create** / **Save changes**.
