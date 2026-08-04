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
            import os
            server_timeout = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "3000"))
            cls.client = MongoClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=server_timeout,
            )
            cls.database = cls.client[settings.DATABASE_NAME]

            print("MongoDB Connected")

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
