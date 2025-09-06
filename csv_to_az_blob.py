from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import os

load_dotenv()

connection_string = os.getenv("blob_container_connection_string")
container_name = "azetlpipelineblob"
json_file_path = "json_file.json"
blob_name = "home_energy_consumption.json" 

blob_service_client = BlobServiceClient.from_connection_string(connection_string)
blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

# upload json file
with open(json_file_path, "rb") as data:
    blob_client.upload_blob(data, overwrite=True)

print("JSON file uploaded to Azure Blob Storage")