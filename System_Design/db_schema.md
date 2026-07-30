# MailSentry – System Design Document

**Version:** 1.0  
**Date:** 2026-07-29  
**Status:** Draft  

---

## 1. Introduction

MailSentry is a web application that enables users to connect their Gmail account, automatically classify incoming emails as **Spam** or **Ham** using a machine learning model, and view the results in an intuitive dashboard. The system stores predictions to avoid reprocessing the same emails and supports searching, filtering, and reporting misclassifications.

This document outlines the complete architecture, data flow, API contracts, database schemas, and implementation details for **Phase 1 (MVP)**.

---

## 2. Requirements

### 2.1 Functional Requirements
- User authentication (email/password or OAuth)
- Connect Gmail account via OAuth 2.0
- Fetch emails from Gmail
- Classify each email as Spam or Ham using an ML model
- Display prediction confidence
- Search and filter emails (by spam/ham/all)
- View full email content
- Report misclassification (feedback loop)
- Logout

### 2.2 Non-Functional Requirements
- **Performance**: Sync and classify 200 emails in < 5 seconds
- **Scalability**: Support hundreds of users and thousands of emails
- **Security**: OAuth tokens encrypted, HTTPS only
- **Maintainability**: Clear separation between frontend, backend, and ML
- **Extensibility**: Architecture allows future features (rankings, summaries, replies)

---

## 3. High-Level Architecture

The system follows a **three-tier architecture**:

- **Frontend**: React SPA – User interface and client-side logic.
- **Backend**: FastAPI (Python) – Handles authentication, Gmail API integration, ML predictions, and database operations.
- **Database**: MongoDB – Stores user profiles, OAuth tokens, email metadata, and predictions.
- **External Services**: Google Gmail API – Fetches emails via OAuth 2.0.
- **ML Pipeline**: Loads preprocessor, model, and label encoder – runs inside the backend (Phase 1).

```mermaid
flowchart LR
    A[React Frontend] -->|HTTPS| B[FastAPI Backend]
    B --> C[(MongoDB)]
    B --> D[Gmail API]
    B --> E[ML Prediction Pipeline]