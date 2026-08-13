import sys
import pandas as pd
import numpy as np
from typing import Optional

from src.configuration.mongo_db_connection import MongoDBClient
from src.constants import DATABASE_NAME
from src.exception import MyException

class FetchMail:
    """
    A class to export MongoDB records as a pandas DataFrame.
    """

    def __init__(self) -> None:
        """
        Initializes the MongoDB client connection.
        """
        try:
            self.mongo_client = MongoDBClient(database_name=DATABASE_NAME)
        except Exception as e:
            raise MyException(e, sys)

    def export_collection_as_dataframe(self, collection_name: str, database_name: Optional[str] = None) -> pd.DataFrame:
        """
        Exports an entire MongoDB collection as a pandas DataFrame.

        Parameters:
        ----------
        collection_name : str
            The name of the MongoDB collection to export.
        database_name : Optional[str]
            Name of the database (optional). Defaults to DATABASE_NAME.

        Returns:
        -------
        pd.DataFrame
            DataFrame containing the collection data, with '_id' column removed and 'na' values replaced with NaN.
        """
        try:
            # Access specified collection from the default or specified database
            if database_name is None:
                collection = self.mongo_client.database[collection_name]
            else:
                collection = self.mongo_client.client[database_name][collection_name]

            # Convert collection data to DataFrame and preprocess
            print("Fetching data from mongoDB")
            df = pd.DataFrame(list(collection.find()))
            print(f"Data fecthed with len: {len(df)}")
                     
            if "_id" in df.columns.to_list():
                df = df.drop(columns=["_id"])
            
            df.replace({"na":np.nan},inplace=True)
            return df

        except Exception as e:
            raise MyException(e, sys)


import json
import os
import pymongo
import certifi
from bson.objectid import ObjectId
from src.constants import (
    MONGODB_URI_REAL_USER,
    DATABASE_NAME_REAL_USER,
    EMAIL_COLLECTION_NAME_REAL_USER,
    INGESTION_STATE_COLLECTION_NAME,
)
from src.logger import logger

ca = certifi.where()


class FetchRealUserMail:
    """
    Class to incrementally fetch real user email records from MongoDB 2
    using _id > last_processed_id checkpointing.
    """

    def __init__(self, db_uri: Optional[str] = None, database_name: Optional[str] = None, collection_name: Optional[str] = None) -> None:
        try:
            self.mongo_uri = db_uri or MONGODB_URI_REAL_USER
            self.db_name = database_name or DATABASE_NAME_REAL_USER
            self.collection_name = collection_name or EMAIL_COLLECTION_NAME_REAL_USER
            self.state_collection_name = INGESTION_STATE_COLLECTION_NAME

            if not self.mongo_uri:
                raise ValueError("MONGODB_URI_REAL_USER environment variable is not set.")

            self.client = pymongo.MongoClient(self.mongo_uri, tlsCAFile=ca)
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            self.state_collection = self.db[self.state_collection_name]
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB 2 connection: {e}")
            raise MyException(e, sys)

    def get_last_processed_id(self, state_file_path: Optional[str] = None) -> Optional[str]:
        """
        Retrieves the last_processed_id checkpoint from MongoDB 2 state collection
        or local state JSON file as fallback.
        """
        try:
            doc = self.state_collection.find_one({"_id": "real_user_email_ingestion"})
            if doc and "last_processed_id" in doc:
                return str(doc["last_processed_id"])

            if state_file_path and os.path.exists(state_file_path):
                with open(state_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("last_processed_id")

            return None
        except Exception as e:
            logger.warning(f"Could not read last_processed_id from DB state collection: {e}. Checking local state file.")
            if state_file_path and os.path.exists(state_file_path):
                try:
                    with open(state_file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        return data.get("last_processed_id")
                except Exception:
                    pass
            return None

    def fetch_new_user_emails(self, last_processed_id: Optional[str] = None, limit: Optional[int] = None) -> list:
        """
        Fetches documents from MongoDB 2 where _id > last_processed_id, sorted by _id ascending.
        """
        try:
            query = {}
            if last_processed_id and str(last_processed_id).strip():
                clean_id = str(last_processed_id).strip()
                if ObjectId.is_valid(clean_id):
                    query["_id"] = {"$gt": ObjectId(clean_id)}
                else:
                    query["_id"] = {"$gt": clean_id}

            logger.info(f"Querying MongoDB 2 collection '{self.collection_name}' with query: {query}")
            cursor = self.collection.find(query).sort("_id", 1)
            if limit and limit > 0:
                cursor = cursor.limit(limit)

            documents = list(cursor)
            logger.info(f"Fetched {len(documents)} new documents from MongoDB 2")
            return documents
        except Exception as e:
            logger.error(f"Error fetching new user emails from MongoDB 2: {e}")
            raise MyException(e, sys)

    def update_last_processed_id(self, new_last_id: str, state_file_path: Optional[str] = None) -> None:
        """
        Updates the last_processed_id checkpoint AFTER successful persistence.
        """
        if not new_last_id:
            return

        clean_id = str(new_last_id).strip()
        try:
            self.state_collection.update_one(
                {"_id": "real_user_email_ingestion"},
                {"$set": {"last_processed_id": clean_id, "updated_at": pd.Timestamp.now().isoformat()}},
                upsert=True,
            )
            logger.info(f"Successfully updated last_processed_id in MongoDB 2 to: {clean_id}")
        except Exception as e:
            logger.warning(f"Could not update last_processed_id in DB state collection: {e}")

        if state_file_path:
            try:
                os.makedirs(os.path.dirname(state_file_path), exist_ok=True)
                with open(state_file_path, "w", encoding="utf-8") as f:
                    json.dump({"last_processed_id": clean_id, "updated_at": pd.Timestamp.now().isoformat()}, f, indent=2)
                logger.info(f"Successfully saved fallback state file to: {state_file_path}")
            except Exception as e:
                logger.error(f"Failed to write state file {state_file_path}: {e}")