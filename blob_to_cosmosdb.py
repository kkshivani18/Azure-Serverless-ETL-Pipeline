# azure funcs

import logging
import json
import azure.functions as func
from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv
import os

load_dotenv()

ENDPOINT = os.getenv("COSMOS_DB_ENDPOINT")
KEY = os.getenv("COSMOS_DB_KEY")
DATABASE_NAME = os.getenv("COSMOS_DB_NAME")
CONTAINER_NAME = os.getenv("COSMOS_CONTAINER_NAME")
PARTITION_KEY_PATH = "/device_id"

def main(blob: func.InputStream):
    try:
        client = CosmosClient(ENDPOINT, KEY)
        database = client.create_database_if_not_exists(id=DATABASE_NAME)
        container = database.create_container_if_not_exists(
            id=CONTAINER_NAME,
            partition_key=PartitionKey(path=PARTITION_KEY_PATH),
            offer_throughput=400
        )

        # read JSON file from blob storage
        blob_json = json.loads(blob.read())
        success_count = 0

        for record in blob_json:  
            try:
                container.upsert_item(record)
                success_count += 1
                logging.info(f"Inserted record with id: {record.get('id', 'N/A')}")
            except Exception as e:
                logging.error(f"Insertion error: {str(e)}")

        logging.info(f"Successfully transferred {success_count} records from Blob to Cosmos DB.")

    except Exception as e:
        logging.error(f"Cosmos DB connection error: {str(e)}")
