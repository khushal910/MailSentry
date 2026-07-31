from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    """This class loads environment variables from a .env file and provides access to them as attributes."""
    
    try:
        APP_NAME = os.getenv("APP_NAME")
        DEBUG = os.getenv("DEBUG") == "True"

        SECRET_KEY = os.getenv("SECRET_KEY")
        ALGORITHM = os.getenv("ALGORITHM")

        ACCESS_TOKEN_EXPIRE_MINUTES = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
        )

        REFRESH_TOKEN_EXPIRE_DAYS = int(
            os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)
        )

        MONGO_URI = os.getenv("MONGO_URI")
        DATABASE_NAME = os.getenv("DATABASE_NAME")
        USER_COLLECTION_NAME = os.getenv("USER_COLLECTION_NAME", "users")
        
        PASSWORD_LENGTH = int(os.getenv("PASSWORD_LENGTH", 8))
        PASSWORD_RULE_APPLY = os.getenv("PASSWORD_RULE_APPLY") == "True"
        
        SECURE_COOKIES = os.getenv("SECURE_COOKIES") == "True"

        # SMTP — email delivery
        SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
        SMTP_PORT     = int(os.getenv("SMTP_PORT", 587))
        SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
        SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
        SMTP_USE_TLS  = os.getenv("SMTP_USE_TLS", "True") == "True"
        EMAIL_FROM    = os.getenv("EMAIL_FROM", "noreply@mailsentry.app")
        EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "MailSentry")
        
        RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", 3))
        RATE_LIMIT_APPLY = os.getenv("RATE_LIMIT_APPLY", "True") == "True"
        RATE_LIMIT_WINDOW_MINUTES  = int(os.getenv("RATE_LIMIT_WINDOW_MINUTES", 15))
        OTP_EXPIRATION_MINUTES = int(os.getenv("OTP_EXPIRATION_MINUTES", 10))

        # Google OAuth
        GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
        GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
        GOOGLE_REDIRECT_URI = os.getenv(
            "GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/auth/google/callback"
        )
        GOOGLE_ACCOUNT_COLLECTION_NAME = os.getenv(
            "GOOGLE_ACCOUNT_COLLECTION_NAME", "GOOGLE_ACCOUNT_COLLECTION_NAME"
        )



    except Exception as e:
        print(f"Error loading environment variables: {str(e)}")

settings = Settings()
