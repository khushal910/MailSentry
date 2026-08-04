import sys

from pandas import DataFrame

from src.logger import logger
from src.exception import MyException
from src.utils.main_utils import read_yaml_file
from src.entity.config_entity import DataValidationConfig


class DataValidation:
    """
    Validates the ingested dataframe using schema.yaml
    """

    def __init__(
        self,
        dataframe: DataFrame,
        data_validation_config: DataValidationConfig = DataValidationConfig(),
    ):
        self.dataframe = dataframe
        self.data_validation_config = data_validation_config

    def validate_data(self) -> bool:
        """
        Validate dataframe against schema.yaml.

        Returns:
            bool: True if validation succeeds else False
        """

        logger.info("Entered validate_data method.")

        try:
            # ==============================
            # Read schema
            # ==============================
            schema = read_yaml_file(
                self.data_validation_config.schema_file_path
            )

            logger.info("Schema file loaded successfully.")

            # ==============================
            # Validate Columns
            # ==============================
            expected_columns = set(schema["columns"].keys())
            actual_columns = set(self.dataframe.columns)

            missing_columns = expected_columns - actual_columns
            extra_columns = actual_columns - expected_columns

            if missing_columns or extra_columns:

                logger.error(
                    f"""
                        Column validation failed.

                        Missing Columns : {missing_columns}

                        Extra Columns   : {extra_columns}
                    """
                )

                return False

            logger.info("Column validation successful.")

            # ==============================
            # Datatype Mapping
            # ==============================
            dtype_mapping = {
                "int": ["int8", "int16", "int32", "int64"],
                "float": ["float16", "float32", "float64"],
                "object": ["object"],
                "category": ["category", "object"],
                "bool": ["bool"],
                "datetime": ["datetime64[ns]"],
            }

            # ==============================
            # Validate Datatypes
            # ==============================
            for column_name, expected_dtype in schema["columns"].items():

                actual_dtype = str(self.dataframe[column_name].dtype)

                if expected_dtype in dtype_mapping:

                    if actual_dtype not in dtype_mapping[expected_dtype]:

                        logger.error(
                            f"""
                                Datatype validation failed.

                                Column Name   : {column_name}

                                Expected Type : {expected_dtype}

                                Actual Type   : {actual_dtype}
                            """
                        )

                        return False

                else:

                    if actual_dtype != expected_dtype:

                        logger.error(
                            f"""
                                Datatype validation failed.

                                Column Name   : {column_name}

                                Expected Type : {expected_dtype}

                                Actual Type   : {actual_dtype}
                            """
                        )

                        return False

            logger.info("Datatype validation successful.")

            logger.info("Data validation completed successfully.")

            return True

        except Exception as e:
            raise MyException(e, sys) from e