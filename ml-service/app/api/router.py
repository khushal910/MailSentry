from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Response, status

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
async def health_check(response: Response):
    engine = MLEngine.get_instance()
    is_ok = engine.is_loaded
    details = engine.metadata.get("details", {})
    if not is_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status="healthy" if is_ok else "unhealthy",
        service=settings.APP_NAME,
        version=engine.version,
        model_loaded=is_ok,
        details={
            "provider": engine.model_type,
            "loaded": is_ok,
            "device": engine.metadata.get("device", "cpu"),
            "models_dir": settings.MODELS_DIR,
            "has_preprocessor": engine.preprocessor is not None,
            "has_label_encoder": engine.label_encoder is not None,
            "classifier_details": details,
        },
    )


@ml_router.get("/ready", tags=["Health"])
@ml_router.get("/api/v1/ready", tags=["Health"])
async def ready_check():
    """
    GET /ready
    Returns HTTP 200 OK only when ML server is running AND inference model is loaded into memory.
    Returns HTTP 503 Service Unavailable if server is running but model is not ready.
    """
    engine = MLEngine.get_instance()
    if engine.is_loaded:
        return {
            "status": "ready",
            "service": settings.APP_NAME,
            "model_version": engine.version,
            "model_type": engine.model_type,
        }

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "status": "not_ready",
            "service": settings.APP_NAME,
            "reason": "Model engine is not loaded into memory",
        },
    )


@ml_router.get("/model/info", tags=["Metadata"])
@ml_router.get("/api/v1/model/info", tags=["Metadata"])
async def model_info_endpoint():
    from app.core.model_registry import get_model_config

    engine = MLEngine.get_instance()
    is_ok = engine.is_loaded
    details = engine.metadata.get("details", {})
    provider = engine.model_type
    config = get_model_config(provider) or {}

    return {
        "model_key": provider,
        "model_name": config.get("name", f"{provider.upper()} Spam Classifier"),
        "provider": config.get("provider", "Hugging Face"),
        "base_model": details.get("base_model", config.get("base_model", provider)),
        "adapter": details.get("adapter", config.get("adapter", "LoRA")),
        "lora_rank": details.get("lora_rank", settings.LORA_R),
        "status": "loaded" if is_ok else "failed",
        "version": engine.version,
        "device": engine.metadata.get("device", "cpu"),
        "target_modules": details.get("target_modules", config.get("target_modules", [])),
    }


@ml_router.get("/version", response_model=VersionResponse, tags=["Metadata"])
@ml_router.get("/api/v1/version", response_model=VersionResponse, tags=["Metadata"])
async def version_info():
    engine = MLEngine.get_instance()
    return VersionResponse(
        service=settings.APP_NAME,
        version="1.0.0",
        model_version=engine.version,
        model_type=engine.metadata.get("model_type", f"{engine.model_type.upper()} Classifier"),
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
        model=result.get("model", engine.model_type),
        probabilities=result.get("probabilities"),
    )


@ml_router.post("/api/v1/model/promote", tags=["Model Lifecycle"])
async def promote_model_endpoint(
    version: str,
    alias: str = "champion",
    x_internal_token: Optional[str] = Header(default=None),
):
    """
    Promote a specific MLflow registered model version to an alias (e.g. @champion).
    """
    verify_service_auth(x_internal_token)
    from src.services.mlflow_model_registry import MLflowModelRegistryService
    from app.services.mlflow_model_loader import MLflowModelLoader

    try:
        reg = MLflowModelRegistryService()
        res = reg.set_model_alias(version=version, alias=alias)
        # Clear in-memory cache to force immediate reload on next prediction
        MLflowModelLoader.clear_cache()
        return {
            "status": "success",
            "message": f"Successfully promoted version {version} to alias @{alias}",
            "details": res,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to promote model version: {e}",
        )


@ml_router.post("/api/v1/model/rollback", tags=["Model Lifecycle"])
async def rollback_model_endpoint(
    version: str,
    alias: str = "champion",
    x_internal_token: Optional[str] = Header(default=None),
):
    """
    Safely rollback the production alias (@champion) to an earlier model version.
    """
    verify_service_auth(x_internal_token)
    from src.services.mlflow_model_registry import MLflowModelRegistryService
    from app.services.mlflow_model_loader import MLflowModelLoader

    try:
        reg = MLflowModelRegistryService()
        res = reg.rollback_alias(target_version=version, alias=alias)
        # Clear in-memory cache to force immediate reload on next prediction
        MLflowModelLoader.clear_cache()
        return {
            "status": "success",
            "message": f"Successfully rolled back alias @{alias} to version {version}",
            "details": res,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to rollback model version: {e}",
        )


@ml_router.get("/api/v1/model/versions", tags=["Model Lifecycle"])
async def list_model_versions_endpoint():
    """
    List all registered versions and active aliases from MLflow Model Registry.
    """
    from src.services.mlflow_model_registry import MLflowModelRegistryService

    try:
        reg = MLflowModelRegistryService()
        versions = reg.list_model_versions()
        return {
            "model_name": reg.model_name,
            "total_versions": len(versions),
            "versions": versions,
        }
    except Exception as e:
        return {
            "model_name": "mailsentry-email-classifier",
            "total_versions": 0,
            "versions": [],
            "error": str(e),
        }

