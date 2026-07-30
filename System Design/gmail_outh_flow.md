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