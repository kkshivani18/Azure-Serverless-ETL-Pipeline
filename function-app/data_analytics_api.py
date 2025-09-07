from function_app import app
import azure.functions as func
import logging
import csv
import uuid
import json
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

@app.route(route="GetAllEnergyData", auth_level=func.AuthLevel.FUNCTION)
def GetAllEnergy(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HttP trigger - Fetching all energy data from CosmosDB")

    try:
        query = "SELECT c.HomeID, c.ApplianceType, c.EnergyConsumption, c.Season, c.Date FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))

        # convert decimal/float serialization 
        return func.HttpResponse(
            body=json.dumps(items, default=str),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error querying CosmosDB: {e}")
        return func.HttpResponse(
            f"Error fetching data: {str(e)}",
            status_code=500
        )