from fastapi import APIRouter, Depends, status
from app.dependencies.auth import get_current_user
from app.schemas.email import ClassifyEmailRequestSchema
from app.services.ml_model_service import MLModelService
from app.utils.main_utile import return_response

classify_router = APIRouter()


@classify_router.post("/classify-email", summary="Classify email content using ML model")
async def classify_email_endpoint(
    request: ClassifyEmailRequestSchema,
    current_user: dict = Depends(get_current_user)
):
    """
    POST /api/classify-email
    Classifies provided email subject and body using the active ML model.
    Requires valid JWT authentication.
    """
    model_service = MLModelService()
    result = model_service.classify_text(subject=request.subject, body=request.body)

    return return_response(
        status_code=status.HTTP_200_OK,
        message="Email classified successfully",
        data=result
    )
