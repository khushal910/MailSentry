import sys
import dagshub
import mlflow
from src.constants import DAGSHUB_USERNAME, DAGSHUB_REPOSITORY, EXPERIMENT_NAME
from src.exception import MyException
from src.logger import logger

# ============================================================================
# Setup MLflow
# ============================================================================

def setup_mlflow() -> None:
    """
    Configure MLflow to use DagsHub as the tracking server.

    Call this only once before starting model training.
    """

    try:

        dagshub.init(
            repo_name=DAGSHUB_REPOSITORY,
            repo_owner=DAGSHUB_USERNAME,
            mlflow=True,
        )

        mlflow.set_tracking_uri(
            f"https://dagshub.com/{DAGSHUB_USERNAME}/{DAGSHUB_REPOSITORY}.mlflow"
        )

        # Create experiment if it doesn't exist
        experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)

        if experiment is None:

            mlflow.create_experiment(EXPERIMENT_NAME)

        mlflow.set_experiment(EXPERIMENT_NAME)

        logger.info("MLflow configured successfully.")

    except Exception as e:

        logger.exception(e)

        raise MyException(e, sys) from e

