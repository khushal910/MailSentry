from langsmith import expect
from pymongo import MongoClient
from app.core.config import settings
from pymongo.database import Database
from app.utils.main_utile import return_response

class MongoDB:

    try:
        
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
    
    except Exception as e:
        print(f"Error in MongoDB class: {str(e)}")
            

try:
    def get_database() -> Database:
        if MongoDB.database is None:
            return return_response(
                status_code=500,
                message="MongoDB is not connected."
            )
        return MongoDB.database
except Exception as e:
    print(f"Error in get_database function: {str(e)}")