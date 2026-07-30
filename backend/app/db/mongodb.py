from pymongo import MongoClient
from app.core.config import settings
from pymongo.database import Database

class MongoDB:

    client: MongoClient | None = None
    database = None

    @classmethod
    def connect(cls):
        cls.client = MongoClient(settings.MONGO_URI)
        cls.database = cls.client[settings.DATABASE_NAME]

        print("MongoDB Connected")

    @classmethod
    def disconnect(cls):
        if cls.client:
            cls.client.close()
            print("MongoDB Disconnected")
            

def get_database() -> Database:
    if MongoDB.database is None:
        raise RuntimeError("MongoDB is not connected.")
    return MongoDB.database