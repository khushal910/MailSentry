import dotenv
import os
dotenv.load_dotenv()

# For MongoDB connection
DATABASE_NAME = os.getenv("DATA_BASE_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
MONGODB_URL_KEY = os.getenv("MONGODB_URI")

# Data Ingestion related constant start with DATA_INGESTION VAR NAME
DATA_INGESTION_COLLECTION_NAME: str = COLLECTION_NAME
DATA_INGESTION_DIR_NAME: str = "data_ingestion"
DATA_INGESTION_FEATURE_STORE_DIR: str = "feature_store"
DATA_INGESTION_INGESTED_DIR: str = "ingested"
DATA_INGESTION_TRAIN_TEST_SPLIT_RATIO: float = 0.25

# Pipeline and artifact related constants
PIPELINE_NAME: str = ""
ARTIFACT_DIR: str = "artifact"

# Model related constants
MODEL_FILE_NAME = "model.pkl"

# Target column for the dataset
TARGET_COLUMN = "fraudulent"

# File related constants
FILE_NAME: str = "data.csv"
TRAIN_FILE_NAME: str = "train.csv"
TEST_FILE_NAME: str = "test.csv"
SCHEMA_FILE_PATH = os.path.join("config", "schema.yaml")

# Backend configuration
BACKEND_DIR_NAME = "backend"
BACKEND_MODEL_PATH_DIR_NAME = "model"