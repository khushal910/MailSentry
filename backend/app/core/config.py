import json
import os

from dotenv import load_dotenv

load_dotenv()


def _parse_cors_origins(val) -> list[str]:
    default_origins = [
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
    """This class loads environment variables from a .env file and provides access to them as attributes."""

    try:
        APP_NAME = os.getenv("APP_NAME", "MailSentry")
        DEBUG = os.getenv("DEBUG") == "True"

        raw_origins = (
            os.getenv("CORS_ORIGINS")
            or os.getenv("COSE_ORIGINS")
            or os.getenv("CORSE_ORIGIN")
        )
        CORS_ORIGINS = _parse_cors_origins(raw_origins)
        COSE_ORIGINS = CORS_ORIGINS  # Alias for backward compatibility
        CORS_ORIGIN_REGEX = os.getenv("CORS_ORIGIN_REGEX", r"https://.*\.vercel\.app")

        SECRET_KEY = os.getenv("SECRET_KEY", "mailsentry-default-secret-key")
        ALGORITHM = os.getenv("ALGORITHM", "HS256")

        ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

        REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

        MONGO_URI = os.getenv("MONGO_URI")
        DATABASE_NAME = os.getenv("DATABASE_NAME")
        USER_COLLECTION_NAME = os.getenv("USER_COLLECTION_NAME", "users")
        EMAIL_COLLECTION_NAME = os.getenv("EMAIL_COLLECTION_NAME", "emails")
        MODEL_COLLECTION_NAME = os.getenv("MODEL_COLLECTION_NAME", "models")
        MODELS_DIR = os.getenv(
            "MODELS_DIR",
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models"
            ),
        )
        MODEL_REGISTRY_DIR = os.getenv(
            "MODEL_REGISTRY_DIR",
            os.path.abspath(
                os.path.join(
                    os.path.dirname(
                        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                    ),
                    "model_registry",
                )
            ),
        )

        PASSWORD_LENGTH = int(os.getenv("PASSWORD_LENGTH", 8))
        PASSWORD_RULE_APPLY = os.getenv("PASSWORD_RULE_APPLY") == "True"

        SECURE_COOKIES = (
            os.getenv("SECURE_COOKIES", "True" if not DEBUG else "False") == "True"
        )
        COOKIE_SAMESITE = os.getenv(
            "COOKIE_SAMESITE", "none" if not DEBUG else "lax"
        ).lower()
        COOKIE_SECURE = SECURE_COOKIES
        if COOKIE_SAMESITE == "none":
            COOKIE_SECURE = True  # SameSite=None requires Secure=True in all browsers

        # SMTP — email delivery
        SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
        SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
        SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
        SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
        SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "True") == "True"
        EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@mailsentry.app")
        EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "MailSentry")

        RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", 3))
        RATE_LIMIT_APPLY = os.getenv("RATE_LIMIT_APPLY", "True") == "True"
        RATE_LIMIT_WINDOW_MINUTES = int(os.getenv("RATE_LIMIT_WINDOW_MINUTES", 15))
        OTP_EXPIRATION_MINUTES = int(os.getenv("OTP_EXPIRATION_MINUTES", 10))

        # Gmail fetch pipeline guards
        # Minimum seconds a user must wait between fetch calls (default 5 min)
        FETCH_RATE_LIMIT_SECONDS = int(os.getenv("FETCH_RATE_LIMIT_SECONDS", 300))
        FETCH_RATE_LIMIT_SECONDS_APPLY = str(
            os.getenv("FETCH_RATE_LIMIT_SECONDS_APPLY", "True")
        ).lower() in ("true", "1", "t")
        # Maximum seconds a per-user concurrency lock may be held before auto-expiry
        FETCH_LOCK_TTL_SECONDS = int(os.getenv("FETCH_LOCK_TTL_SECONDS", 60))
        # Max emails to fetch from Gmail API per fetch operation (default 50)
        FETCH_MAX_RESULTS = int(os.getenv("FETCH_MAX_RESULTS", 50))

        # Google OAuth
        GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
        GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
        GOOGLE_REDIRECT_URI = os.getenv(
            "GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/auth/google/callback"
        )
        GOOGLE_ACCOUNT_COLLECTION_NAME = os.getenv(
            "GOOGLE_ACCOUNT_COLLECTION_NAME", "google_accounts"
        )
        FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8080")

        # LLM Provider & API Configs (Groq default, Gemini secondary)
        LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower().strip()
        GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        # Gemini API Config
        GEMINI_API_KEY = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GEMINI_API")
            or os.getenv("GOOGLE_API_KEY")
            or ""
        )
        GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    except Exception as e:
        print(f"Error loading environment variables: {e!s}")


settings = Settings()
