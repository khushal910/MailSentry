from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class EmailBaseSchema(BaseModel):
    """
    Base Pydantic Schema for Classified Email documents.
    Enforces minimal field storage required for UI (subject, snippet, labels, timestamps).
    """
    user_id: str = Field(..., description="ID of the user in users collection")
    message_id: str = Field(..., min_length=1, description="Unique Gmail message ID")
    thread_id: Optional[str] = Field(default=None, description="Optional Gmail thread ID")
    subject: str = Field(default="", max_length=255, description="Email subject, max 255 chars")
    snippet: Optional[str] = Field(default=None, description="Short snippet preview for UI display")
    predicted_label: str = Field(..., min_length=1, description="Classification result, e.g., 'spam', 'important'")
    predicted_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional classification confidence or probability score"
    )
    fetch_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when email was fetched from Gmail"
    )
    classified_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when classification was completed"
    )

    @field_validator("subject")
    @classmethod
    def validate_subject_length(cls, v: str) -> str:
        if v and len(v) > 255:
            # Truncate to 255 characters to guarantee max length constraint
            return v[:255]
        return v or ""


class EmailCreateSchema(EmailBaseSchema):
    """Schema used when inserting or updating a classified email."""
    pass


class EmailInDBSchema(EmailBaseSchema):
    """Schema representing an email stored in MongoDB."""
    id: Optional[str] = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True


class EmailResponseSchema(EmailBaseSchema):
    """Schema returned by API endpoints for UI consumption."""
    id: Optional[str] = Field(default=None, alias="_id")

    class Config:
        populate_by_name = True
