import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve MongoDB credentials from .env
MONGO_URI = os.getenv("MONGO_URI")  # Example: mongodb+srv://<username>:<password>@<cluster-url>/<database>
DATABASE_NAME = os.getenv("DATABASE_NAME")  # Name of the database
COLLECTION_NAME = os.getenv("COLLECTION_NAME")  # Name of the collection
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "output.json")  # Default output file name

if not MONGO_URI or not DATABASE_NAME or not COLLECTION_NAME:
    print("Error: Missing required environment variables in .env file.")
    exit(1)

def export_data():
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        # Retrieve all documents from the collection
        data = list(collection.find())

        # Convert ObjectId to string for JSON serialization
        for doc in data:
            doc["_id"] = str(doc["_id"])

        # Save data to JSON file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        print(f"Data successfully exported to {OUTPUT_FILE}")

    except Exception as e:
        print(f"An error occurred: {e}")

def export_data_form():
    try:
        # Connect to MongoDB with improved error handling
        print(f"Attempting to connect to MongoDB at {MONGO_URI.split('@')[1] if '@' in MONGO_URI else 'database'}")
        
        # Add certifi for SSL certificate verification and connection options
        import certifi
        client = MongoClient(
            MONGO_URI,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000  # 5 second timeout
        )
        
        # Test the connection
        client.admin.command('ping')
        print("Connected successfully to MongoDB")
        
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        # Structure for the feedback form data
        feedback_schema = {
            "timestamp": "",
            "environment": "",
            "nearby_objects": "",
            "desired_action": "",  # "Remote Control" or "Change Velocity"
            "desired_velocity": "",  # "Slow", "Medium", or "Fast"
            "cause_for_action": "",  # "Environment" or "Nearby Objects"
            "reason_for_action": ""
        }
        
                # Retrieve all documents from the collection
        data = list(collection.find())
        print(f"Retrieved {len(data)} documents from collection")

        # Convert ObjectId to string for JSON serialization
        for doc in data:
            doc["_id"] = str(doc["_id"])

        # Save data to JSON file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        print(f"Data successfully exported to {OUTPUT_FILE}")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please check your MongoDB connection string and network connectivity")
        # Print more detailed error information
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    #export_data()
    export_data_form()
