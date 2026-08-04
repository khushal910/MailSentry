import uvicorn
from fastapi import FastAPI
from app.api.router import auth_router
from fastapi.middleware.cors import CORSMiddleware
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
        from app.services.ml_model_service import MLModelService

        EmailRepository().ensure_indexes()
        ModelRepository().ensure_indexes()
        DashboardRepository().ensure_indexes()
        MLModelService().load_latest_model()
    except Exception as e:
        print(f"Startup initialization warning: {e}")
    yield
    MongoDB.disconnect()



app = FastAPI(
  title="MailSentry API",
  version="1.0.0",
  lifespan=lifespan
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


if(__name__ == "__main__"):
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)