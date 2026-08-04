# MailSentry 🛡️

[![MailSentry CI Pipeline](https://github.com/khushal910/MailSentry/actions/workflows/ci.yml/badge.svg)](https://github.com/khushal910/MailSentry/actions/workflows/ci.yml)
[![MailSentry Production CD](https://github.com/khushal910/MailSentry/actions/workflows/deploy.yml/badge.svg)](https://github.com/khushal910/MailSentry/actions/workflows/deploy.yml)
[![Code Coverage](https://img.shields.io/badge/coverage-80%25%2B-brightgreen.svg)](https://github.com/khushal910/MailSentry/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Node.js Version](https://img.shields.io/badge/node-20.x-green.svg)](https://nodejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com/)
[![React + TypeScript](https://img.shields.io/badge/React-19.0-61DAFB.svg)](https://react.dev/)

> **Real-Time AI Email Classification, Security Guardrails & Automated Threat Intelligence Platform**

MailSentry is an enterprise-grade email classification engine and monitoring system powered by scikit-learn ML models, FastAPI asynchronous backend, and modern React web UI.

---

## 🛠️ Architecture & Tech Stack

* **Frontend**: React 19, TypeScript, Vite, TanStack Router, TanStack Query, TailwindCSS
* **Backend**: Python 3.11, FastAPI, Pydantic v2, Motor / PyMongo, scikit-learn
* **Database**: MongoDB Atlas
* **Machine Learning**: Custom LinearSVC & TF-IDF Vectorizer Pipeline with PredictionEngine caching
* **Cloud Infrastructure**: Vercel Edge (Frontend Web App), Render (FastAPI Cloud API)

---

## 🧪 CI/CD Pipeline & Code Quality

MailSentry uses an enterprise GitHub Actions CI/CD pipeline enforcing zero-defect deployments:

1. **Code Quality & Style**: Automated formatting (`Black`, `isort`, `Prettier`) and linting (`Ruff`, `ESLint`).
2. **Type Safety**: Static type checking via `mypy` and `tsc`.
3. **Automated Testing & Coverage**: Unit test suite with **80% minimum coverage threshold** (`pytest-cov`).
4. **Security Audits**: Automated vulnerability scanning (`Bandit`, `pip-audit`, `npm audit`) and full git history secret leak detection (`Gitleaks`).
5. **ML Validation**: Pre-deployment verification of model weights, artifact hashes, preprocessors, and live inference.
6. **Automated Deployments**: Zero-downtime deployment to Vercel and Render with post-deployment health probes.

---

## 💻 Local Development Setup

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
