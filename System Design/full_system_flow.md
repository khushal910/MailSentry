```mermaid
flowchart TD
    A[User] --> B[Frontend]
    B -->|POST /gmail/sync| C[Backend]
    C --> D[Read Gmail Token from MongoDB]
    D --> E[Gmail API: fetch emails]
    E --> F[Extract Subject + Body]
    F --> G[ML Prediction Pipeline]
    G --> H[TF-IDF + Model]
    H --> I[Prediction: Spam / Ham + Confidence]
    I --> J[Store in MongoDB]
    J --> K[Return Response]
    K --> L[Frontend displays emails]