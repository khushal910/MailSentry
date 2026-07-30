```mermaid

sequenceDiagram
    actor User
    User->>Frontend: Click "Connect Gmail"
    Frontend->>Backend: GET /gmail/connect
    Backend->>Google: Redirect to OAuth consent
    Google-->>User: Authorization page
    User->>Google: Grant permission
    Google-->>Backend: Authorization code
    Backend->>Google: Exchange for access/refresh tokens
    Backend-->>MongoDB: Store tokens for user
    Backend-->>Frontend: Success

    User->>Frontend: Click "Sync Emails"
    Frontend->>Backend: POST /gmail/sync
    Backend->>MongoDB: Get user tokens
    Backend->>Google: Fetch new emails (since last sync)
    Google-->>Backend: List of email objects
    loop For each email
        Backend->>ML Pipeline: predict(subject + body)
        ML Pipeline-->>Backend: prediction & confidence
        Backend->>MongoDB: Store email + prediction
    end
    Backend-->>Frontend: List of classified emails
    Frontend->>User: Display dashboard