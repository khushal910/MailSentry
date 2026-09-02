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

import pandas as pd
from src.components.real_user_ingestion import RealUserIngestion

class DataIngestion:
      def __init__(self):
            """
            :param data_ingestion_config: configuration for data ingestion
            """ 
            try:
                  self.data_ingestion_config = DataIngestionConfig()
            except Exception as e:
                  raise MyException(e,sys)


      def export_data_into_feature_store(self) -> DataFrame:
            """
            Method Name :   export_data_into_feature_store
            Description :   Loads baseline old data (cached locally in old_data/ so it doesn't re-download)
                            and combines it with new real user data from MongoDB 2 into combine_data/data.csv.
            """
            try:
                  old_data_file_path = self.data_ingestion_config.old_data_file_path
                  
                  # 1. Check if baseline old data is already cached locally
                  if os.path.exists(old_data_file_path) and os.path.getsize(old_data_file_path) > 0:
                        logger.info(f"Loading cached baseline old data from local disk: {old_data_file_path}")
                        dataframe = pd.read_csv(old_data_file_path)
                  else:
                        # Check fallback to local raw dataset in data/enron_spam_data.csv
                        fallback_local_csv = os.path.join("data", "enron_spam_data.csv")
                        if os.path.exists(fallback_local_csv) and os.path.getsize(fallback_local_csv) > 0:
                              logger.info(f"Loading baseline old data from local seed file: {fallback_local_csv}")
                              dataframe = pd.read_csv(fallback_local_csv)
                        else:
                              logger.info("Local baseline old data not found. Exporting baseline data from MongoDB 1...")
                              my_data = FetchMail()
                              dataframe = my_data.export_collection_as_dataframe(collection_name=self.data_ingestion_config.collection_name)
                        
                        # Cache it locally in old_data/ so it never needs to be re-downloaded over network
                        os.makedirs(os.path.dirname(old_data_file_path), exist_ok=True)
                        dataframe.to_csv(old_data_file_path, index=False, header=True)
                        logger.info(f"Cached baseline old data locally to: {old_data_file_path}")

                  logger.info(f"Shape of baseline old dataframe: {dataframe.shape}")

                  # 2. Incremental Real User Data Ingestion from MongoDB 2 (new_data/)
                  if self.data_ingestion_config.fetch_real_user_data:
                        logger.info("FETCH_REAL_USER_DATA=True. Triggering incremental real user data ingestion from MongoDB 2.")
                        real_user_ingestion = RealUserIngestion(config=self.data_ingestion_config)
                        real_user_df = real_user_ingestion.ingest_incremental_real_user_data()

                        if not real_user_df.empty:
                              logger.info(f"Combining baseline old data ({len(dataframe)}) with accumulated new real-user dataset ({len(real_user_df)}).")
                              cols = ["Message ID", "Subject", "Message", "Spam/Ham", "Date"]
                              dataframe = pd.concat([dataframe[cols], real_user_df[cols]], ignore_index=True)
                              # Randomly shuffle old and new data rows together rather than appending at the end
                              dataframe = dataframe.sample(frac=1.0, random_state=42).reset_index(drop=True)
                              logger.info(f"Randomly shuffled combined dataset shape: {dataframe.shape}")
                        else:
                              logger.info("No new real-user data available to append. Using baseline old dataset.")
                  else:
                        logger.info("FETCH_REAL_USER_DATA=False. Proceeding with baseline old dataset only.")

                  # 3. Save combined dataset to combine_data/data.csv
                  feature_store_file_path = self.data_ingestion_config.feature_store_file_path
                  dir_path = os.path.dirname(feature_store_file_path)
                  os.makedirs(dir_path, exist_ok=True)

                  logger.info(f"Saving combined data into feature store file path: {feature_store_file_path}")
                  dataframe.to_csv(feature_store_file_path, index=False, header=True)
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
            
   
if __name__ == "__main__":
      try:
            logger.info("Starting data ingestion process")
            data_ingestion = DataIngestion()
            data_ingestion.initiate_data_ingestion()
            logger.info("Data ingestion process completed successfully")
      except Exception as e:
            logger.error(f"Error occurred in data ingestion component: {e}")
            raise MyException(e, sys) from e