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

@app.route(route="GetEnergyDataByID", auth_level=func.AuthLevel.FUNCTION)
def GetEnergyDataByID(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger function received a request.")

    home_id = req.params.get("HomeID")
    if not home_id:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            home_id = req_body.get("HomeID")

    if home_id:
        # query CosmosDB with the HomeID
        return func.HttpResponse(f"Data request received for HomeID: {home_id}")
    else:
        return func.HttpResponse(
            "Please provide HomeID in query string or request body",
            status_code=400
        )
