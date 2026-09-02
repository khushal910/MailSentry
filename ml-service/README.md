# MailSentry ML Service

This directory contains the Machine Learning Service for MailSentry, including data ingestion, validation, transformation, model training, benchmarking, hyperparameter tuning, experiment tracking, and model registry services.

## Pipeline & Architecture Documentation

For complete architectural details, pipeline flow, component breakdowns, design rationale, business impact, and comparative alternatives, please refer to:

👉 **[PIPELINE_ORCHESTRATION.md](./PIPELINE_ORCHESTRATION.md)**

## Pipeline Stages (DVC)

```bash
# Run the complete DVC pipeline
dvc repro
```

1. **Data Ingestion**: `python -m src.components.data_ingestion`
2. **Data Transformation**: `python -m src.components.data_transformation`
3. **Model Training & Benchmarking**: `python -m src.components.model_traning`

## Real User Data Ingestion (MongoDB 2)

To enable incremental real user email data ingestion from MongoDB 2:

### Environment Variable
- `FETCH_REAL_USER_DATA=false` (Default): Pipeline ingests Kaggle baseline dataset from MongoDB 1 only.
- `FETCH_REAL_USER_DATA=true`: Incrementally fetches new real-user emails from MongoDB 2 (`_id > last_processed_id`), deduplicates against existing records, appends valid records to `artifact/data_ingestion/real_user/real_user_curated.csv`, and trains on **Kaggle Baseline + Accumulated Real User Dataset**.

### Weekly Retraining Command

```bash
# Enable real-user data fetch and run data ingestion:
FETCH_REAL_USER_DATA=true python -m src.components.data_ingestion

# Run data transformation and model training:
python -m src.components.data_transformation
python -m src.components.model_traning

# Or run complete pipeline with DVC:
FETCH_REAL_USER_DATA=true dvc repro
```

## Centralized MLflow Model Registry & Promotion

MailSentry uses **MLflow Model Registry** (`mailsentry-email-classifier`) as the single source of truth for versioning, artifacts, alias management (`@champion`, `@staging`), and instant zero-downtime rollbacks.

### Model Retrieval & Caching
- **Model URI:** `models:/mailsentry-email-classifier@champion`
- **Dual-Layer Cache:** In-Memory LRU Cache + Local Disk Cache (`~/.cache/mailsentry_models/`)
- **MongoDB Sync:** MongoDB stores lightweight metadata references only (`mlflow_run_id`, `version`, `git_commit`, `dvc_hash`). No model binary blobs are stored in MongoDB.

### Model Promotion & Rollback Endpoints

```bash
# Promote a registered version (e.g. 18) to @champion
POST http://localhost:9000/api/v1/model/promote?version=18&alias=champion

# Rollback @champion alias to an earlier version (e.g. 17)
POST http://localhost:9000/api/v1/model/rollback?version=17&alias=champion

# List all registered versions and aliases
GET http://localhost:9000/api/v1/model/versions
```

