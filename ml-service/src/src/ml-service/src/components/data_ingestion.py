import sys
import os
from src.data_access.fetch_data import FetchMail
from src.logger import logger
from src.exception import MyException
from src.entity.config_entity import DataIngestionConfig
from sklearn.model_selection import train_test_split
from src.entity.artifact_entity import DataIngestionArtifact
from pandas import DataFrame
from src.components.data_validation import DataValidation
from src.entity.config_entity import DataIngestionConfig

class DataIngestion:
      def __init__(self):
            """
            :param data_ingestion_config: configuration for data ingestion
            """ 
            try:
                  self.data_ingestion_config = DataIngestionConfig()
            except Exception as e:
                  raise MyException(e,sys)


      def export_data_into_feature_store(self)->DataFrame:
            """
            Method Name :   export_data_into_feature_store
            Description :   This method exports data from mongodb to csv file
            
            Output      :   data is returned as artifact of data ingestion components
            On Failure  :   Write an exception log and then raise an exception
            """
            try:
                  logger.info(f"Exporting data from mongodb")
                  
                  my_data = FetchMail()
                  dataframe = my_data.export_collection_as_dataframe(collection_name=self.data_ingestion_config.collection_name)
                  
                  logger.info(f"Shape of dataframe: {dataframe.shape}")
                  
                  feature_store_file_path  = self.data_ingestion_config.feature_store_file_path
                  dir_path = os.path.dirname(feature_store_file_path)
                  os.makedirs(dir_path,exist_ok=True)
                  
                  logger.info(f"Saving exported data into feature store file path: {feature_store_file_path}")
                  
                  dataframe.to_csv(feature_store_file_path,index=False,header=True)
                  return dataframe

            except Exception as e:
                  raise MyException(e,sys)
            

      def split_data_as_train_test_and_store(self,dataframe: DataFrame) ->None:
            """
            Method Name :   split_data_as_train_test_and_store
            Description :   This method splits the dataframe into train set and test set based on split ratio and stores them
            
            Output      :   Folder is created in s3 bucket
            On Failure  :   Write an exception log and then raise an exception
            """
            logger.info("Entered split_data_as_train_test_and_store method of Data_Ingestion class")

            try:
                  train_set, test_set = train_test_split(dataframe, test_size=self.data_ingestion_config.train_test_split_ratio)
                  
                  logger.info("Performed train test split on the dataframe")
                  logger.info("Exited split_data_as_train_test_and_store method of Data_Ingestion class")
                  
                  dir_path = os.path.dirname(self.data_ingestion_config.training_file_path)
                  os.makedirs(dir_path,exist_ok=True)
                  
                  logger.info(f"Exporting train and test file path.")
                  train_set.to_csv(self.data_ingestion_config.training_file_path,index=False,header=True)
                  test_set.to_csv(self.data_ingestion_config.testing_file_path,index=False,header=True)

                  logger.info(f"Exported train and test file path.")
            except Exception as e:
                  raise MyException(e, sys) from e


             
      
      def initiate_data_ingestion(self) ->DataIngestionArtifact:
            """
            Method Name :   initiate_data_ingestion
            Description :   This method initiates the data ingestion components of training pipeline 
            
            Output      :   train set and test set are returned as the artifacts of data ingestion components
            On Failure  :   Write an exception log and then raise an exception
            """
            logger.info("Entered initiate_data_ingestion method of Data_Ingestion class")

            try:
                  dataframe = self.export_data_into_feature_store()
                  
                  # Validate the data and if the data is valid then only perform train test split and store them
                  is_valid = DataValidation(dataframe).validate_data()
                  if not is_valid:
                        logger.error("Data validation failed. Exiting data ingestion process.")
                        raise MyException("Data validation failed.", sys)

                  logger.info("Got the data from mongodb")

                  self.split_data_as_train_test_and_store(dataframe)

                  logger.info("Performed train test split on the dataset")

                  logger.info(
                  "Exited initiate_data_ingestion method of Data_Ingestion class"
                  )

                  data_ingestion_artifact = DataIngestionArtifact(trained_file_path=self.data_ingestion_config.training_file_path,
                  test_file_path=self.data_ingestion_config.testing_file_path)
                  
                  logger.info(f"Data ingestion artifact: {data_ingestion_artifact}")
                  return data_ingestion_artifact
            except Exception as e:
                  raise MyException(e, sys) from e
            
   
try:
      data_ingestion = DataIngestion()
      data_ingestion.initiate_data_ingestion()
except Exception as e:
      logger.error(f"Error occurred in data ingestion component: {e}")
      raise MyException(e, sys) from e