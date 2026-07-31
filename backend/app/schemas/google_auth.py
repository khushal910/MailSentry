from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class GoogleUserProfileSchema(BaseModel):
    """Extracted Google user profile information."""
    google_id: str
    email: EmailStr
    email_verified: bool = False
    name: str | None = None
    picture: str | None = None
    given_name: str | None = None
    family_name: str | None = None

class GoogleTokenPayloadSchema(BaseModel):
    """Google OAuth 2.0 token response payload."""
    access_token: str
    expires_in: int
    id_token: str
    scope: str | None = None
    token_type: str = "Bearer"
    refresh_token: str | None = None

class GoogleAccountSummarySchema(BaseModel):
    """Summary of Google Account linked document in MongoDB."""
    google_email: EmailStr
    google_connected: bool = True
    user_id: str | None = None
    access_token_expiry: str | None = None

class MailSentryUserSummarySchema(BaseModel):
    """Summary of authenticated MailSentry user."""
    id: str
    username: str
    email: EmailStr
    role: str = "user"
    google_connected: bool = True

class GoogleAuthResponseData(BaseModel):
    """Data object returned upon successful Google OAuth callback."""
    user: MailSentryUserSummarySchema
