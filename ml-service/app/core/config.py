import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "MailSentry ML Service")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 9000))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

    # Artifacts & Directory Settings
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    MODELS_DIR: str = os.getenv("MODELS_DIR", os.path.join(BASE_DIR, "models"))
    
    # ML Parameters
    CLASSIFICATION_THRESHOLD: float = float(os.getenv("CLASSIFICATION_THRESHOLD", 0.50))
    
    # Internal Security Token (optional for production service-to-service auth)
    API_KEY_SECRET: str = os.getenv("API_KEY_SECRET", "")
    
    # CORS Origins
    CORS_ORIGINS: list[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]


settings = Settings()
