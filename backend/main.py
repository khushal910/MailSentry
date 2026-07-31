import uvicorn
from fastapi import FastAPI
from app.api.router import auth_router
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db.mongodb import MongoDB


@asynccontextmanager
async def lifespan(app: FastAPI):

    MongoDB.connect()
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
        "http://localhost:3000",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])


if(__name__ == "__main__"):
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)