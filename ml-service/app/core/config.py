import json
import os
from dotenv import load_dotenv

load_dotenv()


def _parse_cors_origins(val) -> list[str]:
    default_origins = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "https://mail-sentry.vercel.app",
    ]
    if not val:
        return default_origins

    if isinstance(val, list):
        parsed_list = [str(item).strip() for item in val if str(item).strip()]
    else:
        val_str = str(val).strip()
        if not val_str:
            return default_origins

        parsed_list = []
        if val_str.startswith("[") and val_str.endswith("]"):
            try:
                parsed = json.loads(val_str)
                if isinstance(parsed, list):
                    parsed_list = [
                        str(item).strip() for item in parsed if str(item).strip()
                    ]
            except Exception:
                parsed_list = []

        if not parsed_list:
            parsed_list = [item.strip() for item in val_str.split(",") if item.strip()]

    valid_origins = [
        o
        for o in parsed_list
        if o == "*" or o.startswith("http://") or o.startswith("https://")
    ]
    return valid_origins if valid_origins else default_origins


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "MailSentry ML Service")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 9000))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

    # Artifacts & Directory Settings
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    MODELS_DIR: str = os.getenv("MODELS_DIR", os.path.join(BASE_DIR, "models"))
    
    # ML Parameters
    CLASSIFICATION_MODEL: str = os.getenv("CLASSIFICATION_MODEL", "mlops").lower().strip()
    CLASSIFICATION_THRESHOLD: float = float(os.getenv("CLASSIFICATION_THRESHOLD", 0.50))
    
    # Internal Security Token (optional for production service-to-service auth)
    API_KEY_SECRET: str = os.getenv("API_KEY_SECRET", "") or os.getenv("ML_SERVICE_API_KEY", "")
    
    # CORS Configuration (configurable via CORS_ORIGINS & CORS_ORIGIN_REGEX in .env)
    raw_origins = (
        os.getenv("CORS_ORIGINS")
        or os.getenv("COSE_ORIGINS")
        or os.getenv("CORSE_ORIGIN")
    )
    CORS_ORIGINS: list[str] = _parse_cors_origins(raw_origins)
    CORS_ORIGIN_REGEX: str = os.getenv("CORS_ORIGIN_REGEX", r"https://.*\.vercel\.app")


settings = Settings()
