from dotenv import load_dotenv
import os

load_dotenv()


class Settings:

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

settings = Settings()