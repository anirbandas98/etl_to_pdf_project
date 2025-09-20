import json
from pymongo import MongoClient
import os

# --- Configuration ---
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "etl_db"
COLLECTION_NAME = "students"
DATA_FILE = "sample_data.json"

def connect_to_mongodb():
    """
    Establishes a connection to the MongoDB database.
    
    Returns:
        pymongo.database.Database: The database object if connection is successful,
                                    None otherwise.
    """
    try:
        # Create a MongoClient to connect to the MongoDB instance.
        client = MongoClient(MONGO_URI)
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        print("Connected to MongoDB successfully!")
        return client.get_database(DB_NAME)
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

def import_data():
    """
    Reads data from a JSON file and inserts it into a MongoDB collection.
    """
    db = connect_to_mongodb()
    
    # Corrected check: check if the database object is None.
    if db is None:
        return

    try:
        # Open the JSON data file.
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        
        collection = db[COLLECTION_NAME]
        
        # Clear any existing data to ensure a clean slate.
        collection.delete_many({})
        
        # Insert the data into the collection.
        if data:
            result = collection.insert_many(data)
            print(f"Successfully inserted {len(result.inserted_ids)} documents into the '{COLLECTION_NAME}' collection.")
        else:
            print("The data file is empty. No documents to import.")

    except FileNotFoundError:
        print(f"Error: The file '{DATA_FILE}' was not found.")
    except json.JSONDecodeError:
        print(f"Error: Failed to decode the JSON file '{DATA_FILE}'. Please check its format.")
    except Exception as e:
        print(f"An unexpected error occurred during data import: {e}")

if __name__ == "__main__":
    import_data()
