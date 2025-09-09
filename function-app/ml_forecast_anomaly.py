from function_app import app
import azure.functions as func
import logging
import os
import json
import joblib
import pandas as pd
from azure.storage.blob import BlobClient
from azure.cosmos import CosmosClient
from prophet.serialize import model_from_json

# cosmos credentials
COSMOSDB_ENDPOINT = os.getenv("COSMOSDB_ENDPOINT")
COSMOSDB_KEY = os.getenv("COSMOSDB_KEY")
DATABASE = os.getenv("COSMOSDB_DATABASE")
CONTAINER = os.getenv("COSMOSDB_CONTAINERML")

# blob container
STORAGE_ACC_CONNECTION_STRING = os.getenv("STORAGE_ACC_CONNECTION_STRING")
MODEL_CONTAINER = os.getenv("MODEL_CONTAINER")
PROPHET_BLOB = os.getenv("PROPHET_BLOB")
ISOFOREST_BLOB = os.getenv("ISOFOREST_BLOB")

# local file paths 
# LOCAL_PROPHET = os.path.join(os.path.dirname(__file__), "tmp/prophet_model.json")
# LOCAL_ISOFOREST = os.path.join(os.path.dirname(__file__), "tmp/anomaly_isoforest.pkl")

LOCAL_PROPHET = os.path.join(os.getcwd(), "tmp", "prophet_model.json")
LOCAL_ISOFOREST = os.path.join(os.getcwd(), "tmp", "anomaly_isoforest.pkl")


# initialize cosmos client
cosmos_client = CosmosClient(COSMOSDB_ENDPOINT, COSMOSDB_KEY)
database = cosmos_client.get_database_client(DATABASE)
container = database.get_container_client(CONTAINER)

# download model from blob to local path
def download_blob_if_missing(blob_conn, container_name, blob_name, target_path):
    if os.path.exists(target_path):
        return
    blob = BlobClient.from_connection_string(blob_conn, container_name, blob_name)
    logging.info(f"Downloading {blob_name} -> {target_path}")
    with open(target_path, "wb") as f:
        f.write(blob.download_blob().readall())

# load models at cold start
try:
    if STORAGE_ACC_CONNECTION_STRING:
        download_blob_if_missing(STORAGE_ACC_CONNECTION_STRING, MODEL_CONTAINER, PROPHET_BLOB, LOCAL_PROPHET)
        download_blob_if_missing(STORAGE_ACC_CONNECTION_STRING, MODEL_CONTAINER, ISOFOREST_BLOB, LOCAL_ISOFOREST)
    else:
        logging.warning("STORAGE_ACC_CONNECTION_STRING not set — expecting local model files packaged with function.")

    # load prophet model
    with open(LOCAL_PROPHET, "r") as f:
        prophet_model = model_from_json(f.read())

    # load isolationforest pipeline
    anomaly_pipeline = joblib.load(LOCAL_ISOFOREST)

    logging.info("Models loaded successfully.")

except Exception as e:
    logging.error(f"Error loading models at startup: {e}")
    prophet_model = None
    anomaly_pipeline = None

# parse query params  
def get_param(req, name, default=None):
    val = req.params.get(name)
    if not val:
        try:
            body = req.get_json()
            val = body.get(name)
        except Exception:
            val = default
    return val if val is not None else default

# Forecasting (with prophet)
@app.route(route="Forecast", auth_level=func.AuthLevel.FUNCTION)
def Forecast(req: func.HttpRequest) -> func.HttpResponse:
    """
    Query params:
      - days (int, optional, default 7)
      - HomeID (optional) -> if provided, you will get per-home aggregated series (but forecast uses the pre-trained global Prophet model)
    """
    if prophet_model is None:
        return func.HttpResponse("Prophet model not loaded.", status_code=500)

    try:
        days = int(get_param(req, "days", 7))
        homeid = get_param(req, "HomeID", None)

        if homeid:
            query = "SELECT c.Date, c.EnergyConsumption FROM c WHERE c.HomeID = @homeid"
            parameters = [{"name":"@homeid","value": homeid}]
            items = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
        else:
            query = "SELECT c.Date, c.EnergyConsumption FROM c"
            items = list(container.query_items(query=query, enable_cross_partition_query=True))

        if not items:
            return func.HttpResponse(json.dumps([]), mimetype="application/json", status_code=200)

        df = pd.DataFrame(items)
        # normalize
        df['Date'] = pd.to_datetime(df['Date'])
        # aggregate to daily
        daily = df.groupby('Date', as_index=False)['EnergyConsumption'].sum()
        daily = daily.rename(columns={'Date':'ds','EnergyConsumption':'y'}).sort_values('ds')

        # IMPORTANT: we will use pre-trained prophet_model (trained on your global daily series).
        # If you want truly per-home forecasts you should train per-home model or use hierarchical forecasting.
        future = prophet_model.make_future_dataframe(periods=days)
        forecast = prophet_model.predict(future)

        # return last `days` forecasts
        forecast_slice = forecast[['ds','yhat','yhat_lower','yhat_upper']].tail(days)
        results = forecast_slice.to_dict(orient='records')
        return func.HttpResponse(body=json.dumps(results, default=str), mimetype="application/json", status_code=200)

    except Exception as e:
        logging.exception("Forecast error")
        return func.HttpResponse(f"Error building forecast: {e}", status_code=500)


# Anomaly Detection (with IsolationForest)
@app.route(route="DetectAnomalies", auth_level=func.AuthLevel.FUNCTION, methods=["POST","GET"])
def DetectAnomalies(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST JSON or query params:
      - HomeID (optional) - if provided, the function will analyze that home; else runs across all homes in the date range
      - start (YYYY-MM-DD)
      - end (YYYY-MM-DD)
    Returns JSON rows with features, score and anomaly flag
    """
    if anomaly_pipeline is None:
        return func.HttpResponse("Anomaly model not loaded.", status_code=500)

    try:
        homeid = get_param(req, "HomeID", None)
        start = get_param(req, "start", None)
        end = get_param(req, "end", None)

        # Build base query
        sql = "SELECT c.HomeID, c.Date, c.EnergyConsumption, c.ApplianceType FROM c"
        where = []
        parameters = []

        if homeid:
            where.append("c.HomeID = @homeid")
            parameters.append({"name":"@homeid","value": homeid})
        if start:
            where.append("c.Date >= @start")
            parameters.append({"name":"@start","value": start})
        if end:
            where.append("c.Date <= @end")
            parameters.append({"name":"@end","value": end})

        if where:
            sql = f"{sql} WHERE " + " AND ".join(where)

        items = list(container.query_items(query=sql, parameters=parameters if parameters else None, enable_cross_partition_query=True))
        if not items:
            return func.HttpResponse(json.dumps([]), mimetype="application/json", status_code=200)

        df = pd.DataFrame(items)
        df['Date'] = pd.to_datetime(df['Date'])

        # Aggregate to per-home, per-day (same features used in training)
        agg = df.groupby(['HomeID','Date']).agg(
            total_kwh = ('EnergyConsumption','sum'),
            unique_appliances = ('ApplianceType','nunique')
        ).reset_index().sort_values(['HomeID','Date'])

        # rolling mean per home (7-day)
        agg['rolling_7_mean'] = agg.groupby('HomeID')['total_kwh'].transform(lambda x: x.rolling(7, min_periods=1).mean())
        agg['dow'] = agg['Date'].dt.dayofweek

        feature_cols = ['total_kwh','unique_appliances','rolling_7_mean','dow']
        X = agg[feature_cols].fillna(0)

        preds = anomaly_pipeline.predict(X)              # -1 anomaly, 1 normal
        scores = anomaly_pipeline.decision_function(X)   # higher = more normal (sklearn)
        agg['anomaly'] = preds == -1
        agg['score'] = scores

        # return useful fields
        out = agg[['HomeID','Date','total_kwh','unique_appliances','rolling_7_mean','dow','score','anomaly']].to_dict(orient='records')
        return func.HttpResponse(body=json.dumps(out, default=str), mimetype="application/json", status_code=200)

    except Exception as e:
        logging.exception("DetectAnomalies error")
        return func.HttpResponse(f"Error running anomaly detection: {e}", status_code=500)