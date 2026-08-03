"""
Model routes for production machine learning model details and status.
"""

from fastapi import APIRouter, status
from app.utils.main_utile import return_response

model_router = APIRouter()


@model_router.get(
    "/model/production",
    summary="Get currently deployed production machine learning model details",
    response_description="Production model specifications, status, and performance metrics",
)
async def get_production_model():
    """
    GET /api/v1/model/production (also accessible at /api/model/production)
    Returns information about the machine learning model currently deployed in production.
    """
    model_data = {
        "model_name": "DistilBERT",
        "version": "v2.1.0",
        "status": "Production",
        "task": "Spam Email Classification",
        "accuracy": 98.42,
        "precision": 98.16,
        "recall": 97.91,
        "f1_score": 98.03,
        "training_date": "2026-08-03",
        "dataset_size": 17880,
        "algorithm_type": "Transformer",
        "description": "Fine-tuned DistilBERT model trained for binary spam classification.",
        "is_active": True,
    }
    return return_response(
        status_code=status.HTTP_200_OK,
        message="Production model details retrieved successfully",
        data=model_data,
    )
