"""
Model REST API routes for production model specifications, history, version details, and comparison.
All endpoints read exclusively from backend/models/ (independent of ml-service).
Sanitizes all internal filesystem paths to produce clean, enterprise-grade production errors.
"""

from fastapi import APIRouter, HTTPException, Query, status

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
    Returns metadata of the current production model, enriched with live ml-service status.
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
        except Exception:
            data["serving_status"] = "Fallback Engine"
            data["ml_service_healthy"] = False

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
    Returns list of all model versions stored in backend/models/ (production + versions).
    """
    try:
        history = storage.get_history()
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
