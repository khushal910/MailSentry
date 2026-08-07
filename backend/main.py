import uvicorn
from fastapi import FastAPI
from app.api.router import auth_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.db.mongodb import MongoDB


@asynccontextmanager
async def lifespan(app: FastAPI):

    MongoDB.connect()
    try:
        from app.repositories.email_repository import EmailRepository
        from app.repositories.model_repository import ModelRepository
        from app.repositories.dashboard_repository import DashboardRepository
        from app.repositories.google_account_repository import GoogleAccountRepository
        from app.services.ml_model_service import MLModelService

        EmailRepository().ensure_indexes()
        ModelRepository().ensure_indexes()
        DashboardRepository().ensure_indexes()
        GoogleAccountRepository().ensure_indexes()

        from app.services.ml_client import MLServiceClient

        try:
            client = MLServiceClient()
            await client.check_health()
            print("Successfully connected to independent ML Service microservice.")
        except Exception as ml_err:
            print(f"ML Service health check probe warning at startup: {ml_err}")
    except Exception as e:
        print(f"Startup initialization warning: {e}")
    yield
    MongoDB.disconnect()



app = FastAPI(
  title="MailSentry API",
  version="1.0.0",
  lifespan=lifespan
)


# -----------------------------------------------------------------------------
# Middleware Configuration
# -----------------------------------------------------------------------------
# GZipMiddleware handles HTTP response compression for eligible responses.
# - What GZipMiddleware does: Automatically compresses outgoing HTTP responses
#   using Gzip compression when the client supports it via the 'Accept-Encoding: gzip' header.
# - Why minimum_size is set to 1000: Setting minimum_size=1000 bytes (1 KB) ensures
#   that small responses (e.g., small JSON status messages, health checks, or auth tokens)
#   are not compressed. Compressing tiny responses adds CPU overhead without meaningful
#   network savings and can even increase payload size due to gzip header overhead.
# - When responses are compressed: Responses are compressed ONLY when:
#     1. The request includes an 'Accept-Encoding: gzip' header.
#     2. The uncompressed response body is >= 1000 bytes.
#     3. The response status code is not 204 No Content or 304 Not Modified.
# - Benefits & Trade-offs:
#     - Benefits: Dramatically reduces network transfer size (up to 70-80% reduction for large
#       JSON lists like emails, logs, or dashboard metrics), resulting in faster page load times,
#       reduced bandwidth costs, and lower latency over mobile/slow connections.
#     - Trade-offs: Slight CPU overhead on the server during compression, which is mitigated by
#       bypassing compression for responses under 1000 bytes.
# -----------------------------------------------------------------------------
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


from app.api.google_auth import google_auth_router
from app.api.google_status import google_status_router
from app.api.gmail_routes import gmail_router
from app.api.classify_email import classify_router
from app.api.emails import emails_router
from app.api.profile_routes import profile_router
from app.api.dashboard_routes import dashboard_router
from app.api.model_routes import model_router

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(google_auth_router, prefix="/auth/google", tags=["Google OAuth"])
app.include_router(google_status_router, prefix="/api/google", tags=["Google Status"])
app.include_router(gmail_router, prefix="/api/gmail", tags=["Gmail"])
app.include_router(classify_router, prefix="/api", tags=["Email Classification"])
app.include_router(emails_router, prefix="/api", tags=["Emails"])
app.include_router(emails_router, tags=["Emails Root"])
app.include_router(profile_router, prefix="/api", tags=["Profile"])
app.include_router(profile_router, prefix="/api/v1", tags=["Profile V1"])
app.include_router(dashboard_router, prefix="/api", tags=["Dashboard"])
app.include_router(model_router, prefix="/api/v1", tags=["Production Model"])
app.include_router(model_router, prefix="/api", tags=["Production Model Base"])




@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "MailSentry API",
        "version": "1.0.0",
        "database": MongoDB.client is not None
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=settings.DEBUG)