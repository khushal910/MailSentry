import logging
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.router import ml_router
from app.core.config import settings
from app.services.ml_engine import MLEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ml_service.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing MailSentry ML Service...")
    engine = MLEngine.get_instance()
    if engine.is_loaded:
        logger.info(f"ML Service ready. Active model version: '{engine.version}'")
    else:
        logger.warning("ML Service started with no active model loaded!")
    yield
    logger.info("Shutting down MailSentry ML Service.")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Independent FastAPI Microservice for MailSentry Machine Learning Inference",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ml_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
