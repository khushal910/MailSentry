import sys
try:
    import pymongo
    import certifi
    ca = certifi.where()
except ImportError:
    pymongo = None
    certifi = None
    ca = None

from src.exception import MyException
from src.logger import logger
from src.constants import DATABASE_NAME, MONGODB_URL_KEY



class MongoDBClient:

    client = None  # Shared MongoClient instance across all MongoDBClient instances

    def __init__(self, database_name: str = DATABASE_NAME) -> None:
        """
        Initializes a connection to the MongoDB database. If no existing connection is found, it establishes a new one.

        Parameters:
        ----------
        database_name : str, optional
            Name of the MongoDB database to connect to. Default is set by DATABASE_NAME constant.

        Raises:
        ------
        MyException
            If there is an issue connecting to MongoDB or if the environment variable for the MongoDB URL is not set.
        """
        try:
            # Check if a MongoDB client connection has already been established; if not, create a new one
            if MongoDBClient.client is None:
                mongo_db_url = MONGODB_URL_KEY # Retrieve MongoDB URL from environment variables
                if mongo_db_url is None:
                    raise Exception(f"Environment variable '{MONGODB_URL_KEY}' is not set.")
                
                # Establish a new MongoDB client connection
                MongoDBClient.client = pymongo.MongoClient(mongo_db_url, tlsCAFile=ca)
                
            # Use the shared MongoClient for this instance
            self.client = MongoDBClient.client
            self.database = self.client[database_name]  # Connect to the specified database
            self.database_name = database_name
            logger.info("MongoDB connection successful.")
            
        except Exception as e:
            # Raise a custom exception with traceback details if connection fails
            raise MyException(e, sys)