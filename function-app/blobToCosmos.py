# transform code 
from function_app import app
import azure.functions as func
import logging
import csv
import uuid
from azure.cosmos import CosmosClient, PartitionKey
import os

# cosmos credentials
COSMOSDB_ENDPOINT = os.getenv("COSMOSDB_ENDPOINT")
COSMOSDB_KEY = os.getenv("COSMOSDB_KEY")
DATABASE = os.getenv("COSMOSDB_DATABASE")
CONTAINER = os.getenv("COSMOSDB_CONTAINERTR")

# initialize cosmos client
client = CosmosClient(COSMOSDB_ENDPOINT, COSMOSDB_KEY)
database = client.create_database_if_not_exists(id=DATABASE)
container = database.create_container_if_not_exists(
    id=CONTAINER,
    partition_key=PartitionKey(path="/HomeID"),
    offer_throughput=400
)

# target schema
REQUIRED_COLS = ["Home ID", "Appliance Type", "Energy Consumption (kWh)", "Season", "Date", "Household Size"]

@app.blob_trigger(arg_name="myblob", path="azetlpipelineblob/{name}", connection="AzureWebJobsStorage")
def BlobToCosmos(myblob: func.InputStream):
    logging.info(f"Processing blob: {myblob.name}, Size: {myblob.length} bytes")

    try:
        # read csv
        blob_bytes = myblob.read()
        blob_text = blob_bytes.decode("utf-8").splitlines()
        reader = csv.DictReader(blob_text)

        # normalize headers
        normalized_fieldnames = [
            h.strip().lower().replace(" ", "").replace("(kwh)", "").replace("(°c)", "")
            for h in reader.fieldnames
        ]
        logging.info(f"Normalized headers: {normalized_fieldnames}")

        # rebuild reader with normalized headers
        reader = csv.DictReader(blob_text, fieldnames=normalized_fieldnames)
        next(reader) 

        transformed_count = 0
        skipped_count = 0

        for row in reader:
            item = {
                "HomeID": row.get("homeid"),
                "ApplianceType": row.get("appliancetype"),
                "Season": row.get("season"),
                "Date": row.get("date"),
                "id": str(uuid.uuid4())
            }

            # numeric conversions
            try:
                item["EnergyConsumption"] = float(row.get("energyconsumption", 0))
            except (ValueError, TypeError):
                item["EnergyConsumption"] = None

            try:
                item["HouseholdSize"] = int(row.get("householdsize", 0))
            except (ValueError, TypeError):
                item["HouseholdSize"] = None

            # validation
            if not item["HomeID"] or not item["ApplianceType"] or item["EnergyConsumption"] is None:
                skipped_count += 1
                continue

            container.create_item(item)
            transformed_count += 1

        logging.info(f"Inserted {transformed_count} records into CosmosDB.")
        logging.info(f"Skipped {skipped_count} invalid rows.")

    except Exception as e:
        logging.error(f"Error processing blob: {str(e)}")
