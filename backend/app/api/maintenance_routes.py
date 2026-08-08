from fastapi import APIRouter
from app.core.config import settings

maintenance_router = APIRouter()


@maintenance_router.get("/maintenance/status", tags=["Maintenance"])
@maintenance_router.get("/v1/maintenance/status", tags=["Maintenance"])
async def get_maintenance_status():
    """
    Public endpoint that returns the current maintenance mode state of the application.
    """
    return {
        "success": True,
        "maintenance": settings.MAINTENANCE_MODE,
        "maintenance_end": settings.MAINTENANCE_END,
        "admin_bypass": settings.MAINTENANCE_ADMIN_BYPASS,
        "message": (
            "Server is currently under maintenance."
            if settings.MAINTENANCE_MODE
            else "Server is operating normally."
        ),
    }
