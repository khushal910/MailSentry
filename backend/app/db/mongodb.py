import os

from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import settings
from app.utils.main_utile import return_response


class MongoDB:

    try:

        client: MongoClient | None = None
        database = None

        @classmethod
        def connect(cls):
            mongo_uri = (
                getattr(settings, "MONGO_URI", None)
                or os.getenv("MONGO_URI")
                or os.getenv("MONGODB_URI")
                or "mongodb://localhost:27017"
            )
            db_name = (
                getattr(settings, "DATABASE_NAME", None)
                or os.getenv("DATABASE_NAME")
                or os.getenv("DATA_BASE_NAME")
                or "mail_sentry_db"
            )
            server_timeout = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "3000"))
            cls.client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=server_timeout,
            )
            cls.database = cls.client[str(db_name)]

            print(f"MongoDB Connected to database '{db_name}'.")

        @classmethod
        def disconnect(cls):
            if cls.client:
                cls.client.close()
                print("MongoDB Disconnected")

    except Exception as e:
        print(f"Error in MongoDB class: {e!s}")


try:

    def get_database() -> Database:
        if MongoDB.database is None:
            return return_response(status_code=500, message="MongoDB is not connected.")
        return MongoDB.database

except Exception as e:
    print(f"Error in get_database function: {e!s}")
