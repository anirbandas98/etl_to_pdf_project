import json
import logging
import os
from datetime import datetime
from pymongo import MongoClient

# --- Configuration ---
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "etl_db"
COLLECTION_NAME = "students"
DATA_FILE_PATH = "sample_data.json"

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("etl_process.log"),
        logging.StreamHandler()
    ]
)

def connect_to_mongodb():
    """
    Establishes a connection to the MongoDB database.

    Returns:
        MongoClient: The MongoClient object, or None if connection fails.
    """
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ismaster')
        logging.info("Connected to MongoDB successfully!")
        return client
    except Exception as e:
        logging.error(f"Error connecting to MongoDB: {e}", exc_info=True)
        return None

def load_data_from_file(file_path):
    """
    Loads data from a specified JSON file.

    Args:
        file_path (str): The path to the JSON data file.

    Returns:
        list: A list of dictionaries containing the data, or an empty list if loading fails.
    """
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            logging.info(f"Successfully loaded data from '{file_path}'.")
            return data
    except FileNotFoundError:
        logging.error(f"Error: The file '{file_path}' was not found. Please ensure it exists.", exc_info=True)
        return []
    except json.JSONDecodeError:
        logging.error(f"Error: The file '{file_path}' is not a valid JSON file.", exc_info=True)
        return []
    except Exception as e:
        logging.error(f"An unexpected error occurred while loading data: {e}", exc_info=True)
        return []

def import_data_to_mongodb(client, data, db_name, collection_name):
    """
    Ingests data into a specified MongoDB collection.

    Args:
        client (MongoClient): The MongoDB client object.
        data (list): The list of dictionaries to import.
        db_name (str): The name of the database.
        collection_name (str): The name of the collection.
    """
    try:
        db = client.get_database(db_name)
        collection = db[collection_name]
        
        # Clear existing data
        collection.delete_many({})
        logging.info(f"Clearing existing data from '{collection_name}' collection...")
        
        # Insert the new data
        if data:
            collection.insert_many(data)
            logging.info(f"Successfully inserted {len(data)} records into '{collection_name}' collection.")
        else:
            logging.warning("No data to insert.")
        
    except Exception as e:
        logging.error(f"An error occurred during data ingestion: {e}", exc_info=True)

def main():
    """
    Main function to run the data ingestion process.
    """
    logging.info("--- Starting Data Ingestion Process ---")
    client = connect_to_mongodb()
    
    if client:
        try:
            # Load data from the JSON file
            sample_data = load_data_from_file(DATA_FILE_PATH)
            
            # Import data into MongoDB
            import_data_to_mongodb(client, sample_data, DB_NAME, COLLECTION_NAME)
        
        finally:
            client.close()
            logging.info("MongoDB connection closed.")
    else:
        logging.error("Failed to connect to MongoDB. Data ingestion process aborted.")
        
    logging.info("--- Data Ingestion Process Finished ---")

if __name__ == "__main__":
    main()
