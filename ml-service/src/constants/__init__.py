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
BACKEND_MODEL_PATH_DIR_NAME = "models"

# Data Transformation related constants
DATA_TRANSFORMATION_DIR_NAME = "data_transformation"
DATA_TRANSFORMATION_TRANSFORMED_TRAIN_FILE = "transformed_train.csv"
DATA_TRANSFORMATION_TRANSFORMED_TEST_FILE = "transformed_test.csv"
DATA_TRANSFORMATION_TRANSFORMED_TRAIN_TFIDF_FILE = "transformed_train_tfidf.csv"
DATA_TRANSFORMATION_TRANSFORMED_TEST_TFIDF_FILE = "transformed_test_tfidf.csv"
DATA_TRANSFORMATION_TRANSFORMED_TRAIN_RAW_FILE = "transformed_train_raw.csv"
DATA_TRANSFORMATION_TRANSFORMED_TEST_RAW_FILE = "transformed_test_raw.csv"
DATA_TRANSFORMATION_PREPROCESSOR_FILE = "preprocessing.pkl"
LABEL_ENCODER_FILE_NAME = "label_encoder.pkl"


# Model training related constants
TARGET_COLUMN = "target"
MODEL_TRAINER_DIR_NAME = "model_trainer"
MODEL_FILE_NAME = "model.pkl"
MODEL_REPORT_FILE_NAME = "model_report.yaml"
MODEL_EVALUATE_METRIC = "f1"
ENABLE_FINE_TUNING: bool = os.getenv("ENABLE_FINE_TUNING", "true").lower() in ("true", "1", "yes", "t")

# Model Registry constants
MODEL_REGISTRY_DIR_NAME = "model_registry"
MODEL_REGISTRY_CHAMPION_DIR = "champion"
MODEL_REGISTRY_ARCHIVE_DIR = "archive"

# MLflow configuration
DAGSHUB_USERNAME =  os.getenv("DAGSHUB_USERNAME")
DAGSHUB_REPOSITORY =  os.getenv("DAGSHUB_REPOSITORY")
EXPERIMENT_NAME =  os.getenv("EXPERIMENT_NAME")