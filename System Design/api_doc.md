# MailSentry API Reference

**Version:** 1.0  
**Base URL:** `https://api.mailsentry.com/api/v1`  
**Content-Type:** `application/json`  
**Authentication:** JWT Bearer Token (except Authentication and OAuth callback endpoints)

---

# Table of Contents

1. Authentication
2. Gmail OAuth
3. Gmail Sync
4. Email Management
5. Error Handling
6. Authentication
7. Rate Limiting
8. Versioning
9. cURL Examples
10. Future Features

---

# 1. Authentication Endpoints

## 1.1 Register User

**Endpoint**

```http
POST /auth/register
```

### Description

Creates a new user account.

### Request Body

```json
{
  "email": "user@example.com",
  "password": "your_secure_password"
}
```

### Response (201 Created)

```json
{
  "message": "User registered successfully",
  "user_id": "60f7a0b8c1d2e3f4a5b6c7d8"
}
```

### Error Responses

| Status | Description |
|---------|-------------|
| 400 | Email already exists or validation failed |

---

## 1.2 Login

**Endpoint**

```http
POST /auth/login
```

### Description

Authenticates the user and returns access and refresh tokens.

### Request Body

```json
{
  "email": "user@example.com",
  "password": "your_secure_password"
}
```

### Response (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Error Responses

| Status | Description |
|---------|-------------|
| 401 | Invalid credentials |

---

## 1.3 Refresh Access Token

**Endpoint**

```http
POST /auth/refresh
```

### Description

Returns a new access token using a refresh token.

### Request Body

```json
{
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4..."
}
```

### Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Error Responses

| Status | Description |
|---------|-------------|
| 401 | Invalid or expired refresh token |

---

## 1.4 Logout

**Endpoint**

```http
POST /auth/logout
```

### Authentication

Required

### Description

Invalidates the current refresh token.

### Request Body

None

### Response

```json
{
  "message": "Logged out successfully"
}
```

---

# 2. Gmail OAuth Endpoints

## 2.1 Connect Gmail

**Endpoint**

```http
GET /gmail/connect
```

### Authentication

Required

### Description

Redirects the authenticated user to Google's OAuth Consent Screen.

### Query Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| redirect_uri | No | Frontend callback URL |

### Response

```
302 Redirect → Google OAuth
```

---

## 2.2 OAuth Callback

**Endpoint**

```http
GET /gmail/oauth/callback
```

### Authentication

Not Required

### Description

Google redirects here after user authorization.

### Query Parameters

| Parameter | Description |
|-----------|-------------|
| code | Authorization code |
| state | User/session identifier |

### Success

- Closes popup
- Redirects back to frontend
- Displays success page

### Error Responses

| Status | Description |
|---------|-------------|
| 400 | Missing code or state |
| 500 | Token exchange failed |

---

# 3. Gmail Sync Endpoint

## 3.1 Sync Emails

**Endpoint**

```http
POST /gmail/sync
```

### Authentication

Required

### Description

- Fetch new Gmail emails
- Run ML prediction
- Store emails in database
- Update last sync time

### Request Body

None

### Response

```json
{
  "synced": 42,
  "new_spam": 12,
  "last_sync": "2026-07-30T10:00:00Z"
}
```

### Error Responses

| Status | Description |
|---------|-------------|
| 401 | Unauthorized |
| 404 | Gmail not connected |
| 500 | Gmail API or ML failure |

---

# 4. Email Management Endpoints

## 4.1 Get Emails

**Endpoint**

```http
GET /emails
```

### Authentication

Required

### Description

Returns paginated emails with filtering.

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| filter | string | all | all, spam, ham |
| search | string | - | Search subject, sender, body |
| page | integer | 1 | Page number |
| limit | integer | 20 | Max 100 |
| sort | string | date | Sort field |
| order | string | desc | asc or desc |

### Response

```json
{
  "emails": [
    {
      "_id": "60f7a0...",
      "gmail_id": "18fd3...",
      "subject": "Win an iPhone",
      "sender": "abc@gmail.com",
      "date": "2026-07-28T12:00:00Z",
      "snippet": "Click this link...",
      "prediction": "spam",
      "confidence": 0.98,
      "is_manual_override": false
    }
  ],
  "total": 100,
  "page": 1,
  "limit": 20,
  "total_pages": 5
}
```

### Error Responses

| Status | Description |
|---------|-------------|
| 401 | Unauthorized |

---

## 4.2 Get Single Email

**Endpoint**

```http
GET /emails/{emailId}
```

### Authentication

Required

### Path Parameters

| Parameter | Description |
|-----------|-------------|
| emailId | MongoDB Email ID |

### Response

```json
{
  "_id": "60f7a0...",
  "user_id": "60f7a0...",
  "gmail_id": "18fd3...",
  "thread_id": "...",
  "subject": "Win an iPhone",
  "sender": "abc@gmail.com",
  "receiver": "user@example.com",
  "date": "2026-07-28T12:00:00Z",
  "snippet": "Click this link...",
  "body_text": "Full message text...",
  "prediction": "spam",
  "confidence": 0.98,
  "model_version": "v1.0",
  "is_manual_override": false,
  "created_at": "2026-07-28T12:05:00Z"
}
```

### Error Responses

| Status | Description |
|---------|-------------|
| 401 | Unauthorized |
| 404 | Email not found |

---

## 4.3 Report Wrong Prediction

**Endpoint**

```http
POST /emails/{emailId}/report
```

### Authentication

Required

### Path Parameters

| Parameter | Description |
|-----------|-------------|
| emailId | MongoDB Email ID |

### Request Body

```json
{
  "correct_label": "ham"
}
```

> Allowed values:
>
> - spam
> - ham

### Response

```json
{
  "message": "Feedback recorded successfully"
}
```

### Error Responses

| Status | Description |
|---------|-------------|
| 400 | Invalid label |
| 401 | Unauthorized |
| 404 | Email not found |

---

# 5. Error Handling

Every error follows this format:

```json
{
  "detail": "Human-readable error message",
  "code": "ERROR_CODE"
}
```

## HTTP Status Codes

| Code | Meaning |
|------|----------|
| 200 | OK |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

---

# 6. Authentication

All endpoints except:

- `/auth/*`
- `/gmail/oauth/callback`

require JWT authentication.

Use:

```http
Authorization: Bearer <access_token>
```

Access tokens expire after a certain time.

Use:

```http
POST /auth/refresh
```

to obtain a new token.

---

# 7. Rate Limiting

| Endpoint | Limit |
|-----------|-------|
| POST /gmail/sync | 5 requests/hour |
| POST /auth/login | 10 requests/minute |
| GET /emails | 100 requests/minute |
| Others | 60 requests/minute |

Exceeded requests return:

```http
429 Too Many Requests
```

---

# 8. Versioning

Current API version:

```text
/api/v1
```

Breaking changes will be released under future versions.

Example:

```
/api/v2
```

---

# 9. cURL Examples

## Login

```bash
curl -X POST https://api.mailsentry.com/api/v1/auth/login \
-H "Content-Type: application/json" \
-d '{"email":"user@example.com","password":"secret"}'
```

---

## Sync Emails

```bash
curl -X POST https://api.mailsentry.com/api/v1/gmail/sync \
-H "Authorization: Bearer <access_token>"
```

---

## Fetch Spam Emails

```bash
curl -X GET "https://api.mailsentry.com/api/v1/emails?filter=spam&page=2&limit=50" \
-H "Authorization: Bearer <access_token>"
```

---

# 10. Future Features

## Webhooks

Future releases will support webhooks for:

- New spam detection
- Email classification events
- Third-party integrations
- Real-time notifications