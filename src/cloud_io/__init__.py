import pandas as pd
import pymongo
import os, sys
import certifi
from src.constants import *
from src.exception import CustomException

class MongoIO:
    mongo_ins = None

    def __init__(self):
        if MongoIO.mongo_ins is None:
            mongo_db_url = os.getenv(MONGODB_URL_KEY)
            if mongo_db_url is None:
                raise Exception(f"Environment key: {MONGODB_URL_KEY} is not set.")
            
            client = pymongo.MongoClient(mongo_db_url, tlsCAFile=certifi.where())
            
            MongoIO.mongo_ins = client[MONGO_DATABASE_NAME]
        
        self.db = MongoIO.mongo_ins

    def store_reviews(self, product_name: str, reviews: pd.DataFrame):
        try:
            collection_name = product_name.replace(" ", "_")
            data_dict = reviews.to_dict(orient="records")
            if data_dict:
                self.db[collection_name].insert_many(data_dict)
        except Exception as e:
            raise CustomException(e, sys)

    def get_reviews(self, product_name: str):
        try:
            collection_name = product_name.replace(" ", "_")
            data = list(self.db[collection_name].find())
            return data
        except Exception as e:
            raise CustomException(e, sys)