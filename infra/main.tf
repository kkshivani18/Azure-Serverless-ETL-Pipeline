terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "4.42.0"
    }
  }
}

provider "azurerm" {
  features {}
  resource_provider_registrations = "none"
  subscription_id = var.az_subscription_id
}

# resource "azurerm_resource_group" "az_etlpipeline_rg" {
#   name     = var.resource_group_name
#   location = var.location
# }

# storage acc
resource "azurerm_storage_account" "az_storage_account" {
  name                     = var.az_storage_account
  resource_group_name      = azurerm_resource_group.az_etlpipeline_rg.name
  location                 = azurerm_resource_group.az_etlpipeline_rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    environment = "staging"
  }
}

# blob container
resource "azurerm_storage_container" "az_blob_container" {
  name                  = var.az_blob_container
  storage_account_name  = azurerm_storage_account.az_storage_account.name 
  container_access_type = "private"
}

# cosmosdb
resource "azurerm_cosmosdb_account" "az_cosmosdb_acc" {
  name                = var.cosmos_account_name
  location            = azurerm_resource_group.az_etlpipeline_rg.location
  resource_group_name = azurerm_resource_group.az_etlpipeline_rg.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"     

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = azurerm_resource_group.az_etlpipeline_rg.location
    failover_priority = 0
  }
}

# output "cosmos_db_connection_string" {
#   value     = azurerm_cosmosdb_account.az_cosmosdb_acc.primary_key
#   sensitive = true
# }

resource "azurerm_cosmosdb_sql_database" "az_cosmosdb" {
  name                = var.az_cosmosdb
  resource_group_name = azurerm_resource_group.az_etlpipeline_rg.name
  account_name        = azurerm_cosmosdb_account.az_cosmosdb_acc.name
  throughput          = 400                   
}

resource "azurerm_cosmosdb_sql_container" "az_cosmosdb_blob" {
  name                  = var.az_blob_container
  resource_group_name   = azurerm_resource_group.az_etlpipeline_rg.name
  account_name          = azurerm_cosmosdb_account.az_cosmosdb_acc.name
  database_name         = azurerm_cosmosdb_sql_database.az_cosmosdb.name
  partition_key_paths   = ["/home_id"]
  partition_key_version = 1
  throughput            = 400

  indexing_policy {
    indexing_mode = "consistent"
  }

  unique_key {
    paths = ["/definition/idlong", "/definition/idshort"]
  }
}

# app service plan
resource "azurerm_service_plan" "function_plan" {
  name                = var.az_service_plan
  location            = azurerm_resource_group.az_etlpipeline_rg.location
  resource_group_name = azurerm_resource_group.az_etlpipeline_rg.name
  os_type             = "Linux"
  sku_name            = "Y1"   
}

resource "azurerm_storage_account" "function_storage" {
  name                     = var.az_func_stracc
  resource_group_name      = azurerm_resource_group.az_etlpipeline_rg.name
  location                 = azurerm_resource_group.az_etlpipeline_rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# functions app
resource "azurerm_linux_function_app" "az_function_app" {
  name                = var.az_functionapp
  resource_group_name = azurerm_resource_group.az_etlpipeline_rg.name
  location            = azurerm_resource_group.az_etlpipeline_rg.location

  # func storage account 
  storage_account_name       = azurerm_storage_account.function_storage.name
  storage_account_access_key = azurerm_storage_account.function_storage.primary_access_key

  # consumption plan for serverless billing
  service_plan_id            = azurerm_service_plan.function_plan.id

    site_config {
    application_stack {
      python_version = "3.9"  
    }
  }

   app_settings = {
    FUNCTIONS_WORKER_RUNTIME       = "python"
    AzureWebJobsStorage            = azurerm_storage_account.function_storage.primary_connection_string
    CosmosDBConnection             = azurerm_cosmosdb_account.az_cosmosdb_acc.primary_key
    AzureWebJobsFeatureFlags       = "EnableWorkerIndexing"
    WEBSITE_RUN_FROM_PACKAGE       = "1"
  }
}

