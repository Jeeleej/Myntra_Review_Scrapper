import os
import pandas as pd


class MongoIO:
    def __init__(self):
        try:
            from pymongo import MongoClient
            mongo_url = os.environ.get("MONGO_DB_URL", "")
            if not mongo_url:
                raise ValueError("MONGO_DB_URL not set")
            self.client = MongoClient(mongo_url)
            self.db = self.client["ajio_reviews"]
        except Exception as e:
            raise RuntimeError(f"MongoDB connection failed: {e}")

    def store_reviews(self, product_name: str, reviews: pd.DataFrame):
        collection = self.db[product_name.replace(" ", "_")]
        records = reviews.to_dict("records")
        collection.insert_many(records)

    def get_reviews(self, product_name: str) -> pd.DataFrame:
        collection = self.db[product_name.replace(" ", "_")]
        data = list(collection.find({}, {"_id": 0}))
        return pd.DataFrame(data)
