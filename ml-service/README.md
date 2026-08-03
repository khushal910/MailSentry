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
