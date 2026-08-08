import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.utils.main_utile import decode_token

PUBLIC_PATHS = {
    "/health",
    "/api/health",
    "/api/maintenance/status",
    "/api/v1/maintenance/status",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
}


def is_whitelisted_path(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    if path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi"):
        return True
    return False


class MaintenanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces Global Maintenance Mode when MAINTENANCE_MODE=true.

    When maintenance mode is enabled:
    - Allows whitelisted public endpoints (health, maintenance status, OpenAPI docs).
    - Checks admin bypass if MAINTENANCE_ADMIN_BYPASS=true.
    - Intercepts all other requests and returns HTTP 503 Service Unavailable.
    """

    async def dispatch(self, request: Request, call_next):
        if not settings.MAINTENANCE_MODE:
            return await call_next(request)

        # CORS preflight OPTIONS requests must always be allowed through
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path

        if is_whitelisted_path(path):
            return await call_next(request)

        if settings.MAINTENANCE_ADMIN_BYPASS:
            is_admin = await self._check_is_admin(request)
            if is_admin:
                return await call_next(request)

        response_data = {
            "success": False,
            "maintenance": True,
            "message": "MailSentry is currently undergoing scheduled maintenance. Please try again later.",
        }
        if settings.MAINTENANCE_END:
            response_data["maintenance_end"] = settings.MAINTENANCE_END

        return JSONResponse(
            status_code=503,
            content=response_data,
            headers={"Retry-After": "300"},
        )

    async def _check_is_admin(self, request: Request) -> bool:
        if not settings.MAINTENANCE_ADMIN_EMAILS:
            return False

        try:
            token = request.cookies.get("access_token")
            if not token:
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ", 1)[1].strip()

            path = request.url.path.rstrip("/")
            if not token:
                if path.endswith("/auth/login") or path.endswith("/login"):
                    try:
                        body_bytes = await request.body()
                        async def receive():
                            return {"type": "http.request", "body": body_bytes}
                        request._receive = receive

                        if body_bytes:
                            body = json.loads(body_bytes.decode("utf-8"))
                            email = (body.get("email") or "").strip().lower()
                            if email and email in settings.MAINTENANCE_ADMIN_EMAILS:
                                return True
                    except Exception:
                        pass
                return False

            payload = decode_token(token)
            user_id = payload.get("user_id") or payload.get("sub")

            email = str(payload.get("email", "")).strip().lower()
            if email and email in settings.MAINTENANCE_ADMIN_EMAILS:
                return True

            if user_id:
                try:
                    from bson import ObjectId
                    from app.db.mongodb import get_database
                    db = get_database()
                    users_col = db[settings.USER_COLLECTION_NAME]
                    if ObjectId.is_valid(user_id):
                        db_user = users_col.find_one({"_id": ObjectId(user_id)})
                    else:
                        db_user = users_col.find_one({"_id": user_id})

                    if db_user:
                        user_email = str(db_user.get("email", "")).strip().lower()
                        if user_email in settings.MAINTENANCE_ADMIN_EMAILS:
                            return True
                except Exception:
                    pass

        except Exception:
            pass
        return False



