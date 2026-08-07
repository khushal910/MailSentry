from fastapi import APIRouter, Header, HTTPException, status
from typing import Optional

from app.core.config import settings
from app.schemas.predict import (
    HealthResponse,
    PredictRequest,
    PredictResponse,
    VersionResponse,
)
from app.services.ml_engine import MLEngine

ml_router = APIRouter()


def verify_service_auth(x_internal_token: Optional[str] = Header(default=None)):
    if settings.API_KEY_SECRET:
        if not x_internal_token or x_internal_token != settings.API_KEY_SECRET:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing internal service authorization token.",
            )


@ml_router.get("/health", response_model=HealthResponse, tags=["Health"])
@ml_router.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    engine = MLEngine.get_instance()
    is_ok = engine.is_loaded
    return HealthResponse(
        status="healthy" if is_ok else "degraded",
        service=settings.APP_NAME,
        version=engine.version,
        model_loaded=is_ok,
        details={
            "models_dir": settings.MODELS_DIR,
            "has_preprocessor": engine.preprocessor is not None,
            "has_label_encoder": engine.label_encoder is not None,
        },
    )


@ml_router.get("/version", response_model=VersionResponse, tags=["Metadata"])
@ml_router.get("/api/v1/version", response_model=VersionResponse, tags=["Metadata"])
async def version_info():
    engine = MLEngine.get_instance()
    return VersionResponse(
        service=settings.APP_NAME,
        version="1.0.0",
        model_version=engine.version,
        model_type=engine.metadata.get("model_type", "TFIDF + LogisticRegression"),
        metrics=engine.metadata.get("metrics", {}),
        schema_info=engine.schema,
    )


@ml_router.post(
    "/predict", response_model=PredictResponse, tags=["Inference"]
)
@ml_router.post(
    "/api/v1/predict", response_model=PredictResponse, tags=["Inference"]
)
async def predict_endpoint(
    request: PredictRequest,
    x_internal_token: Optional[str] = Header(default=None),
):
    verify_service_auth(x_internal_token)
    engine = MLEngine.get_instance()
    
    subject = request.subject or ""
    body = request.get_text_body()
    
    result = engine.predict(
        subject=subject, body=body, threshold=request.threshold
    )

    return PredictResponse(
        subject=result["subject"],
        predicted_label=result["predicted_label"],
        predicted_score=result["predicted_score"],
        classified_at=result["classified_at"],
        version=result.get("version", engine.version),
    )
