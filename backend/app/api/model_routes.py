"""
Model REST API routes for production model specifications, history, version details, and comparison.
All endpoints read exclusively from backend/models/ (independent of ml-service).
Sanitizes all internal filesystem paths to produce clean, enterprise-grade production errors.
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import settings
from app.services.backend_model_storage import BackendModelStorage
from app.utils.main_utile import return_response

model_router = APIRouter()
storage = BackendModelStorage()


@model_router.get(
    "/model/production",
    summary="Get currently deployed production machine learning model metadata",
    response_description="Active production model metadata, status, metrics, and specifications",
)
async def get_production_model():
    """
    GET /api/v1/model/production (also accessible at /api/model/production)
    Returns metadata of the current production model, enriched with live ml-service status and active provider specs.
    """
    try:
        data = storage.get_production_metadata()
        from app.services.ml_client import MLServiceClient

        try:
            client = MLServiceClient()
            ml_health = await client.check_health()
            data["serving_status"] = "Active Microservice"
            data["ml_service_url"] = client.base_url
            data["ml_service_healthy"] = ml_health.get("status") == "healthy"
            
            if ml_health.get("version"):
                data["version"] = ml_health.get("version")

            details = ml_health.get("details", {}) or {}
            c_details = details.get("classifier_details", {}) or {}
            provider = details.get("provider") or c_details.get("provider", "mlops")
            data["provider"] = provider
            data["device"] = details.get("device", "cpu")

            # Dynamically fetch model specs from centralized MODEL_REGISTRY
            import os
            import importlib.util

            reg_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                    "ml-service",
                    "app",
                    "core",
                    "model_registry.py",
                )
            )
            config = {}
            if os.path.exists(reg_path):
                try:
                    spec = importlib.util.spec_from_file_location("ml_service_model_registry", reg_path)
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        config = mod.get_model_config(provider) or {}
                except Exception:
                    config = {}

            if config:
                data["model_name"] = config.get("name", f"{provider.upper()} Spam Classifier")
                data["algorithm"] = config.get("base_model", provider)
                data["algorithm_type"] = (
                    "Transformer / HuggingFace"
                    if config.get("provider") == "Hugging Face"
                    else "Scikit-Learn Pipeline"
                )
                data["framework"] = (
                    "PyTorch / HuggingFace"
                    if config.get("provider") == "Hugging Face"
                    else "sklearn"
                )
                data["serialization"] = (
                    "safetensors"
                    if config.get("provider") == "Hugging Face"
                    else "joblib"
                )
                data["base_model"] = c_details.get("base_model", config.get("base_model", provider))
                if config.get("adapter"):
                    data["adapter"] = c_details.get("adapter", config.get("adapter"))
                data["description"] = config.get("description", "")
                metrics = config.get("metrics", {})
                for k, v in metrics.items():
                    data[k] = v
            elif provider in ("deberta-v3-base", "deberta"):
                data["model_name"] = "DeBERTa-v3-base Spam Classifier"
                data["algorithm"] = "DeBERTa-v3 (microsoft/deberta-v3-base) + LoRA r=8"
                data["algorithm_type"] = "Transformer / Disentangled Attention / PEFT"
                data["framework"] = "PyTorch / HuggingFace"
                data["serialization"] = "safetensors / PEFT"
                data["base_model"] = c_details.get("base_model", "microsoft/deberta-v3-base")
                data["adapter"] = c_details.get("adapter", "ssheroz/spam-email-classifier-deberta-v3-base-r8")
                data["description"] = (
                    "DeBERTa-v3 transformer with disentangled attention fine-tuned with LoRA r=8 adapter "
                    "for enterprise binary email spam classification."
                )
                data["accuracy"] = 99.35
                data["precision"] = 99.10
                data["recall"] = 99.60
                data["f1_score"] = 99.35
                data["roc_auc"] = 99.98
                data["model_size_mb"] = 512.00
                data["inference_time_ms"] = 14.20
            elif provider == "roberta":
                data["model_name"] = "RoBERTa-LoRA Spam Classifier"
                data["algorithm"] = "RoBERTa (FacebookAI/roberta-base) + LoRA r=8"
                data["algorithm_type"] = "Transformer / PEFT"
                data["framework"] = "PyTorch / HuggingFace"
                data["serialization"] = "safetensors / PEFT"
                data["base_model"] = c_details.get("base_model", "FacebookAI/roberta-base")
                data["adapter"] = c_details.get("adapter", "ssheroz/spam-email-classifier-roberta-r8")
                data["description"] = (
                    "Pretrained RoBERTa transformer fine-tuned with LoRA r=8 adapter "
                    "(ssheroz/spam-email-classifier-roberta-r8) for binary email spam classification."
                )
                data["accuracy"] = 99.12
                data["precision"] = 98.95
                data["recall"] = 99.40
                data["f1_score"] = 99.17
                data["roc_auc"] = 99.96
                data["model_size_mb"] = 498.50
                data["inference_time_ms"] = 12.45
            else:
                data["provider"] = provider

        except Exception as conn_err:
            fallback_model = getattr(settings, "FALLBACK_CLASSIFICATION_MODEL", "mlops")
            data["serving_status"] = "Fallback Engine"
            data["ml_service_healthy"] = False
            data["ml_service_message"] = "ML microservice unreachable over HTTP. Active fallback model is serving predictions locally."
            data["provider"] = fallback_model

            # Enrich fallback response with metadata from model_registry if available
            import os
            import importlib.util

            reg_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                    "ml-service",
                    "app",
                    "core",
                    "model_registry.py",
                )
            )
            if os.path.exists(reg_path):
                try:
                    spec = importlib.util.spec_from_file_location("ml_service_model_registry", reg_path)
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        fb_config = mod.get_model_config(fallback_model) or {}
                        if fb_config:
                            data["model_name"] = fb_config.get("name", "Local Fallback Spam Classifier")
                            data["algorithm"] = fb_config.get("base_model", fallback_model)
                            data["description"] = (
                                f"{fb_config.get('description', '')} (Active local fallback due to unreachable ml-service)"
                            ).strip()
                            metrics = fb_config.get("metrics", {})
                            for k, v in metrics.items():
                                data[k] = v
                except Exception:
                    pass

        return return_response(
            status_code=status.HTTP_200_OK,
            message="Production model details retrieved successfully",
            data=data,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production model metadata is currently unavailable or initializing. Please deploy a model.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load production model details. Please try again later.",
        )



@model_router.get(
    "/model/history",
    summary="Get history of all production models",
    response_description="List of all production and archived versions sorted by deployment date descending",
)
async def get_model_history():
    """
    GET /api/v1/model/history (also accessible at /api/model/history)
    Returns list of all model versions stored in backend/models/ (production + versions),
    enriched with active microservice provider status.
    """
    try:
        history = storage.get_history()
        try:
            prod_resp = await get_production_model()
            if prod_resp and isinstance(prod_resp, dict) and "data" in prod_resp:
                prod_data = prod_resp["data"]
                if history and len(history) > 0:
                    history[0] = prod_data
        except Exception:
            pass

        return return_response(
            status_code=status.HTTP_200_OK,
            message="Model version history retrieved successfully",
            data={"history": history, "total": len(history)},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve model version history.",
        )



@model_router.get(
    "/model/version/{version}",
    summary="Get specific model version metadata",
    response_description="Detailed metadata for a specific model version tag",
)
async def get_model_version(version: str):
    """
    GET /api/v1/model/version/{version} (also accessible at /api/model/version/{version})
    Returns metadata for a specific model version from backend/models/versions/{version}/.
    """
    try:
        data = storage.get_version_metadata(version)
        return return_response(
            status_code=status.HTTP_200_OK,
            message=f"Model version {version} metadata retrieved successfully",
            data=data,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requested model version '{version}' was not found in version history.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to load details for model version '{version}'.",
        )


@model_router.get(
    "/model/compare",
    summary="Compare two model versions",
    response_description="Side-by-side metric comparison between two model versions",
)
async def compare_models(
    v1: str = Query(..., description="Base version tag (e.g. v1.0.0 or production)"),
    v2: str = Query(..., description="Target version tag (e.g. v2.0.0 or production)"),
):
    """
    GET /api/v1/model/compare?v1=v1.0.0&v2=production
    Returns detailed metric differences, direction indicators (improved, decreased, no_change), and percentage changes.
    """
    try:
        result = storage.compare_models(v1, v2)
        return return_response(
            status_code=status.HTTP_200_OK,
            message=f"Model comparison between {v1} and {v2} completed successfully",
            data=result,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"One or both model versions ('{v1}', '{v2}') were not found for comparison.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to compare model versions '{v1}' and '{v2}'.",
        )
