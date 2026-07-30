```mermaid
flowchart TD
    subgraph "Data Sources"
        A[(MongoDB)]
        B[Gmail API]
    end

    subgraph "Training Pipeline"
        C[Data Ingestion]
        D[Data Validation]
        E[Data Transformation<br/>- Clean Text<br/>- TF-IDF<br/>- Label Encoding]
        F[Model Training<br/>- Multiple Classifiers<br/>- Hyperparameter Tuning]
        G[Model Evaluation<br/>- Metrics: accuracy, f1, roc_auc<br/>- MLflow Tracking]
        H[Select Best Model<br/>Based on config metric]
        I[Compare with Production Model<br/>- Load existing model<br/>- Evaluate on test set<br/>- Compare scores]
        J{Is New Model Better?}
        K[Save as Production Model<br/>- model.pkl<br/>- preprocessor.pkl<br/>- label_encoder.pkl]
    end

    subgraph "Production"
        L[Production Model API<br/>- Load artifacts at startup<br/>- Predict endpoint]
        M[Email Sync Service<br/>- Fetch new emails<br/>- Call predict]
        N[(Emails Collection)]
    end

    subgraph "Feedback Loop"
        O[User Reports Misclassification]
        P[Log Feedback<br/>- Store corrected labels]
        Q[Retrain Trigger<br/>- Periodic or on-demand]
    end

    A -->|export_data| C
    B -->|fetch emails| M

    C --> D
    D -->|valid data| E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
    J -->|Yes| K
    J -->|No| L
    K -->|deploy| L

    L -->|predict| M
    M -->|store results| N

    O --> P
    P --> Q
    Q -->|collect feedback data| C

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#f9f,stroke:#333,stroke-width:2px
    style L fill:#bbf,stroke:#333,stroke-width:2px