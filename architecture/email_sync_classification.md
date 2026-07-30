```mermaid
sequenceDiagram
    actor User
    User->>Frontend: Click "Sync Emails"
    Frontend->>Backend: POST /gmail/sync
    Backend->>MongoDB: Get user tokens & last_sync
    Backend->>Google: Fetch new emails (after last_sync)
    Google-->>Backend: List of email objects
    loop For each email
        Backend->>ML Pipeline: predict(subject + body)
        ML Pipeline-->>Backend: prediction & confidence
        Backend->>MongoDB: Store email + prediction
    end
    Backend-->>Frontend: Synced count & new spam count
    Frontend->>User: Display updated dashboard