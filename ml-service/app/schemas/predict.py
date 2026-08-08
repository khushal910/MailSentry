from typing import Any, Optional
from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    subject: Optional[str] = Field(default="", description="Email subject text")
    body: Optional[str] = Field(default="", description="Email body or content text")
    email_body: Optional[str] = Field(default=None, description="Alias for body")
    threshold: Optional[float] = Field(
        default=None, description="Optional classification probability decision threshold"
    )

    def get_text_body(self) -> str:
        if self.body and self.body.strip():
            return self.body
        if self.email_body and self.email_body.strip():
            return self.email_body
        return ""


class PredictResponse(BaseModel):
    subject: str = Field(description="Email subject")
    predicted_label: str = Field(description="Classification result ('spam' or 'safe')")
    predicted_score: float = Field(description="Prediction probability or confidence score")
    classified_at: str = Field(description="ISO 8601 timestamp when prediction was computed")
    version: Optional[str] = Field(default="v1.0.0", description="Active model version")
    model: Optional[str] = Field(default="mlops", description="Active model provider ('mlops' or 'roberta')")
    probabilities: Optional[dict[str, float]] = Field(default=None, description="Class probabilities dictionary")



class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    model_loaded: bool
    details: Optional[dict[str, Any]] = None


class VersionResponse(BaseModel):
    service: str
    version: str
    model_version: Optional[str] = None
    model_type: Optional[str] = None
    metrics: Optional[dict[str, Any]] = None
    schema_info: Optional[dict[str, Any]] = None
