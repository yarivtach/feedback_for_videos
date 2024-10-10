from pymongo import MongoClient, errors
from dotenv import load_dotenv
import logging
import os

class Database:
    def __init__(self):
        load_dotenv()
        mongo_uri = os.getenv('MONGO_URI')
        print(f"\n---------Mongo URI: {mongo_uri}")
        self.db = None
        try:
            client = MongoClient(mongo_uri)
            # Ping the server to ensure the connection is alive
            client.admin.command('ping')
            db_name = mongo_uri.split('/')[-1].split('?')[0]
            print(f"Database name extracted: '{db_name}'")  # Debug print
            if not db_name:
                raise ValueError("Database name is empty. Check your MONGO_URI.")
            self.db = client[db_name]
            print(f"Connected to MongoDB at {mongo_uri}, Database: {db_name}")
        except errors.ConnectionFailure as e:
            logging.error("Failed to connect to MongoDB: Connection Failure", exc_info=True)
            raise e
        except Exception as e:
            logging.error("Failed to connect to MongoDB", exc_info=True)
            raise e

    def insert_data(self, collection_name, data):
        if self.db is not None:
            collection = self.db[collection_name]
            result = collection.insert_one(data)
            logging.info(f"Inserted data into {collection_name}: {result.inserted_id}")
            return result
        else:
            logging.error("Database connection not initialized.")
            raise Exception("Database connection not initialized.")

    def get_data(self, collection_name):
        collection = self.db[collection_name]
        data = list(collection.find({}))
        logging.info(f"Retrieved data from {collection_name}: {data}")
        return data
    
    def save_feedback(self, data):
        return self.db.feedback.insert_one(data)
    
    def retrieve_feedback(self):
        return list(self.db.feedback.find({}))
