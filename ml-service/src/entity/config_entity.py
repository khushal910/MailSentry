import os

from src.constants import *
from dataclasses import dataclass
from typing import Any, Any, Dict

@dataclass
class TrainingPipelineConfig:
    pipeline_name: str = PIPELINE_NAME
    artifact_dir: str = os.path.join(ARTIFACT_DIR)
    bakend_dir: str = BACKEND_DIR_NAME


training_pipeline_config: TrainingPipelineConfig = TrainingPipelineConfig()


@dataclass
class DataIngestionConfig:
    data_ingestion_dir: str = os.path.join(training_pipeline_config.artifact_dir, DATA_INGESTION_DIR_NAME)
    
    # Old baseline data directory and local cached file
    old_data_dir: str = os.path.join(data_ingestion_dir, DATA_INGESTION_OLD_DATA_DIR)
    old_data_file_path: str = os.path.join(old_data_dir, OLD_DATA_FILE_NAME)
    
    # New real-user data directory and files
    new_data_dir: str = os.path.join(data_ingestion_dir, DATA_INGESTION_NEW_DATA_DIR)
    real_user_curated_file_path: str = os.path.join(new_data_dir, REAL_USER_CURATED_FILE_NAME)
    ingestion_state_file_path: str = os.path.join(new_data_dir, INGESTION_STATE_FILE_NAME)
    
    # Combined data directory and combined dataset
    combine_data_dir: str = os.path.join(data_ingestion_dir, DATA_INGESTION_COMBINE_DATA_DIR)
    feature_store_file_path: str = os.path.join(combine_data_dir, FILE_NAME)
    
    # Combined train/test split directory and split files
    combine_train_test_split_dir: str = os.path.join(data_ingestion_dir, DATA_INGESTION_TRAIN_TEST_SPLIT_DIR)
    training_file_path: str = os.path.join(combine_train_test_split_dir, TRAIN_FILE_NAME)
    testing_file_path: str = os.path.join(combine_train_test_split_dir, TEST_FILE_NAME)
    
    train_test_split_ratio: float = DATA_INGESTION_TRAIN_TEST_SPLIT_RATIO
    collection_name: str = DATA_INGESTION_COLLECTION_NAME
    fetch_real_user_data: bool = FETCH_REAL_USER_DATA
    real_user_db_name: str = DATABASE_NAME_REAL_USER
    real_user_collection_name: str = EMAIL_COLLECTION_NAME_REAL_USER

@dataclass
class DataValidationConfig:
    schema_file_path: str = SCHEMA_FILE_PATH

@dataclass
class DataTransformationConfig:
    data_transform_dir: str = os.path.join(training_pipeline_config.artifact_dir, DATA_TRANSFORMATION_DIR_NAME)
    transform_train_file: str = os.path.join(training_pipeline_config.artifact_dir, DATA_TRANSFORMATION_DIR_NAME, DATA_TRANSFORMATION_TRANSFORMED_TRAIN_FILE)
    transform_test_file: str = os.path.join(training_pipeline_config.artifact_dir, DATA_TRANSFORMATION_DIR_NAME, DATA_TRANSFORMATION_TRANSFORMED_TEST_FILE)
    transform_train_tfidf_file: str = os.path.join(training_pipeline_config.artifact_dir, DATA_TRANSFORMATION_DIR_NAME, DATA_TRANSFORMATION_TRANSFORMED_TRAIN_TFIDF_FILE)
    transform_test_tfidf_file: str = os.path.join(training_pipeline_config.artifact_dir, DATA_TRANSFORMATION_DIR_NAME, DATA_TRANSFORMATION_TRANSFORMED_TEST_TFIDF_FILE)
    transform_train_raw_file: str = os.path.join(training_pipeline_config.artifact_dir, DATA_TRANSFORMATION_DIR_NAME, DATA_TRANSFORMATION_TRANSFORMED_TRAIN_RAW_FILE)
    transform_test_raw_file: str = os.path.join(training_pipeline_config.artifact_dir, DATA_TRANSFORMATION_DIR_NAME, DATA_TRANSFORMATION_TRANSFORMED_TEST_RAW_FILE)
    preprocessor_file: str = os.path.join(training_pipeline_config.artifact_dir, DATA_TRANSFORMATION_DIR_NAME, DATA_TRANSFORMATION_PREPROCESSOR_FILE)
    label_encoder_file_path: str = os.path.join(training_pipeline_config.artifact_dir, DATA_TRANSFORMATION_DIR_NAME, LABEL_ENCODER_FILE_NAME)

    

@dataclass
class TrainModelConfig:
    model_trainer_dir: str = os.path.join(training_pipeline_config.artifact_dir,MODEL_TRAINER_DIR_NAME)
    trained_model_file_path: str = os.path.join(model_trainer_dir,MODEL_FILE_NAME)
    model_report_file_path: str = os.path.join(model_trainer_dir,MODEL_REPORT_FILE_NAME)
    preprocessor_file_backend_path: str = os.path.join(training_pipeline_config.bakend_dir, BACKEND_MODEL_PATH_DIR_NAME, DATA_TRANSFORMATION_PREPROCESSOR_FILE)
    trained_model_backend_path: str = os.path.join(training_pipeline_config.bakend_dir, BACKEND_MODEL_PATH_DIR_NAME, MODEL_FILE_NAME)
    model_evaluate_metric: str = MODEL_EVALUATE_METRIC
    model_registry_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", MODEL_REGISTRY_DIR_NAME))
    checkpoints_dir: str = os.path.join(model_trainer_dir, "checkpoints")
    training_state_file_path: str = os.path.join(model_trainer_dir, "training_state.yaml")
    enable_fine_tuning: bool = ENABLE_FINE_TUNING
    enable_distilbert: bool = ENABLE_DISTILBERT
    enable_tabpfn: bool = ENABLE_TABPFN

   
   
@dataclass(frozen=True)
class _ModelBundle:
    """Container for a model, its logging parameters, and optional cross-validation score."""

    name: str
    model: Any
    params: Dict[str, Any]
    best_cv_score: float = 0.0



@dataclass(frozen=True)
class _ModelEvaluation:
    """Container for a trained model and its evaluation metrics."""

    name: str
    model: Any
    params: Dict[str, Any]
    metrics: Dict[str, float]
