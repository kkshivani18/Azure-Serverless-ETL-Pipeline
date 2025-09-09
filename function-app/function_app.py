# global import for funcs file

import azure.functions as func
app = func.FunctionApp()

import blobToCosmos
import data_analytics_api
import ml_forecast_anomaly