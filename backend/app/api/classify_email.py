from fastapi import APIRouter, Depends, status
from app.dependencies.auth import get_current_user
from app.schemas.email import ClassifyEmailRequestSchema
from app.services.ml_model_service import MLModelService
from app.utils.main_utile import return_response

classify_router = APIRouter()


@classify_router.post("/classify-email", summary="Classify email content using ML model")
@classify_router.post("/v1/predict", summary="Classify email content (alias)")
@classify_router.post("/predict", summary="Classify email content (alias)")
async def classify_email_endpoint(
    request: ClassifyEmailRequestSchema,
    current_user: dict = Depends(get_current_user)
):
    """
    Classifies provided email subject and body/message using the active ML model.
    Requires valid JWT authentication.
    """
    model_service = MLModelService()
    result = model_service.classify_text(subject=request.subject, body=request.email_body)

    return return_response(
        status_code=status.HTTP_200_OK,
        message="Email classified successfully",
        data=result
    )

