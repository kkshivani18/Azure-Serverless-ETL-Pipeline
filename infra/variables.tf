variable "resource_group_name" {
    default = "azure-etl-pipeline"
}

variable "location" {
  default = "centralus"
}

variable "az_storage_account" {
  default = "azetlpipelinestr"
}

variable "az_blob_container" {
    default = "azetlpipelineblob"
}

variable "cosmos_account_name" {
  default = "az-etl-pipeline-cosmosdb"
}

variable "az_cosmosdb" {
    default = "az-jsondb"
}

variable "az_subscription_id" {
  description = "value"
  type = string
}

variable "az_service_plan" {
  default = "az_service_plan_func"
}

variable "az_func_stracc" {
  default = "azetlfuncstr"
}

variable "az_functionapp" {
  default = "azetlfunctionapp"
}