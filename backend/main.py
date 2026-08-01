import uvicorn
from fastapi import FastAPI
from app.api.router import auth_router
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db.mongodb import MongoDB


@asynccontextmanager
async def lifespan(app: FastAPI):

    MongoDB.connect()
    try:
        from app.repositories.email_repository import EmailRepository
        from app.repositories.model_repository import ModelRepository
        from app.services.ml_model_service import MLModelService

        EmailRepository().ensure_indexes()
        ModelRepository().ensure_indexes()
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
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


from app.api.google_auth import google_auth_router
from app.api.google_status import google_status_router
from app.api.gmail_routes import gmail_router
from app.api.classify_email import classify_router

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(google_auth_router, prefix="/auth/google", tags=["Google OAuth"])
app.include_router(google_status_router, prefix="/api/google", tags=["Google Status"])
app.include_router(gmail_router, prefix="/api/gmail", tags=["Gmail"])
app.include_router(classify_router, prefix="/api", tags=["Email Classification"])



if(__name__ == "__main__"):
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)