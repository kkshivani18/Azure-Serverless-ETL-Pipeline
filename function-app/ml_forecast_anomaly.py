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
import pickle
import json

# cosmos credentials
COSMOSDB_ENDPOINT = os.getenv("COSMOSDB_ENDPOINT")
COSMOSDB_KEY = os.getenv("COSMOSDB_KEY")
DATABASE = os.getenv("COSMOSDB_DATABASE")
CONTAINER = os.getenv("COSMOSDB_CONTAINERTR")

# blob container
STORAGE_ACC_CONNECTION_STRING = os.getenv("STORAGE_ACC_CONNECTION_STRING")
MODEL_CONTAINER = os.getenv("MODEL_CONTAINER")
PROPHET_BLOB = os.getenv("PROPHET_BLOB")
ISOFOREST_BLOB = os.getenv("ISOFOREST_BLOB")

prophet_model = None
anomaly_pipeline = None

# local file paths 
script_dir = os.path.dirname(__file__)
LOCAL_PROPHET = os.path.join(script_dir, "prophet_model.json")
LOCAL_ISOFOREST = os.path.join(script_dir, "anomaly_isoforest.pkl")

logging.info(f"Checking for Prophet model at: {LOCAL_PROPHET}")
logging.info(f"Checking for IsoForest model at: {LOCAL_ISOFOREST}")

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

    try:
        with open(LOCAL_PROPHET, 'r') as f:
            json_str = f.read()
            prophet_model = model_from_json(json_str)
        logging.info("Prophet model loaded successfully.")

        # with open(LOCAL_ISOFOREST, 'rb') as f:
        # joblib.dump(LOCAL_ISOFOREST)
        anomaly_pipeline = joblib.load(LOCAL_ISOFOREST)
        if isinstance(anomaly_pipeline, dict) and "model" in anomaly_pipeline:
            anomaly_pipeline = anomaly_pipeline["model"]
        # anomaly_pipeline = joblib.load(LOCAL_ISOFOREST)
        print("IsoForest model loaded successfully.")

    except FileNotFoundError as e:
        print(f"Error loading model: {e}")
        # Consider logging the full path to aid debugging
        print(f"Prophet path checked: {LOCAL_PROPHET}")
        print(f"IsoForest path checked: {LOCAL_ISOFOREST}")

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
        # daily = df.groupby('Date', as_index=False)['EnergyConsumption'].sum()
        # daily = daily.rename(columns={'Date':'ds','EnergyConsumption':'y'}).sort_values('ds')

        df['Date'] = pd.to_datetime(df['Date'], format="%d-%m-%Y")
        daily = df.groupby('Date')['EnergyConsumption'].sum()

        # Fill missing dates
        full_range = pd.date_range(start=daily.index.min(), end=daily.index.max(), freq='D')
        daily = daily.reindex(full_range, fill_value=0).reset_index()
        daily.columns = ['ds', 'y']

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
# @app.route(route="DetectAnomalies", auth_level=func.AuthLevel.FUNCTION, methods=["POST","GET"])
# def DetectAnomalies(req: func.HttpRequest) -> func.HttpResponse:
#     """
#     POST JSON or query params:
#       - HomeID (optional) - if provided, the function will analyze that home; else runs across all homes in the date range
#       - start (YYYY-MM-DD)
#       - end (YYYY-MM-DD)
#     Returns JSON rows with features, score and anomaly flag
#     """
#     if anomaly_pipeline is None:
#         return func.HttpResponse("Anomaly model not loaded.", status_code=500)

#     try:
#         homeid = get_param(req, "HomeID", None)
#         start = get_param(req, "start", None)
#         end = get_param(req, "end", None)

#         # Build base query
#         sql = "SELECT c.HomeID, c.Date, c.EnergyConsumption, c.ApplianceType FROM c"
#         where = []
#         parameters = []

#         if homeid:
#             where.append("c.HomeID = @homeid")
#             parameters.append({"name":"@homeid","value": homeid})
#         if start:
#             where.append("c.Date >= @start")
#             parameters.append({"name":"@start","value": start})
#         if end:
#             where.append("c.Date <= @end")
#             parameters.append({"name":"@end","value": end})

#         if where:
#             sql = f"{sql} WHERE " + " AND ".join(where)

#         items = list(container.query_items(query=sql, parameters=parameters if parameters else None, enable_cross_partition_query=True))
#         if not items:
#             return func.HttpResponse(json.dumps([]), mimetype="application/json", status_code=200)

#         df = pd.DataFrame(items)
#         df['Date'] = pd.to_datetime(df['Date'])

#         # Aggregate to per-home, per-day (same features used in training)
#         # agg = df.groupby(['HomeID','Date']).agg(
#         #     total_kwh = ('EnergyConsumption','sum'),
#         #     unique_appliances = ('ApplianceType','nunique')
#         # ).reset_index().sort_values(['HomeID','Date'])

#         df['Date'] = pd.to_datetime(df['Date'], format="%d-%m-%Y")

#         # Initial aggregation
#         agg = df.groupby(['HomeID','Date']).agg(
#             total_kwh=('EnergyConsumption','sum'),
#             unique_appliances=('ApplianceType','nunique')
#         ).reset_index()

#         # Fill missing dates per HomeID
#         filled = []
#         for home in agg['HomeID'].unique():
#             sub = agg[agg['HomeID'] == home].set_index('Date')
#             full_range = pd.date_range(start=sub.index.min(), end=sub.index.max(), freq='D')
#             sub = sub.reindex(full_range, fill_value=0)
#             sub['HomeID'] = home
#             sub = sub.reset_index().rename(columns={'index':'Date'})
#             filled.append(sub)

#         agg = pd.concat(filled).sort_values(['HomeID','Date'])

#         # rolling mean per home (7-day)
#         agg['rolling_7_mean'] = agg.groupby('HomeID')['total_kwh'].transform(lambda x: x.rolling(7, min_periods=1).mean())
#         agg['dow'] = agg['Date'].dt.dayofweek

#         feature_cols = ['total_kwh','unique_appliances','rolling_7_mean','dow']
#         X = agg[feature_cols].fillna(0)

#         preds = anomaly_pipeline.predict(X)              # -1 anomaly, 1 normal
#         scores = anomaly_pipeline.decision_function(X)   # higher = more normal (sklearn)
#         agg['anomaly'] = preds == -1
#         agg['score'] = scores

#         # return useful fields
#         out = agg[['HomeID','Date','total_kwh','unique_appliances','rolling_7_mean','dow','score','anomaly']].to_dict(orient='records')
#         return func.HttpResponse(body=json.dumps(out, default=str), mimetype="application/json", status_code=200)

#     except Exception as e:
#         logging.exception("DetectAnomalies error")
#         return func.HttpResponse(f"Error running anomaly detection: {e}", status_code=500)


# @app.route(route="DetectAnomalies", auth_level=func.AuthLevel.FUNCTION, methods=["POST", "GET"])
# def DetectAnomalies(req: func.HttpRequest) -> func.HttpResponse:
#     """
#     Query params or POST JSON:
#       - HomeID (optional): analyze one home or all homes
#       - start (YYYY-MM-DD): start date filter
#       - end (YYYY-MM-DD): end date filter
#       - debug=true (optional): enables logging of intermediate steps
#     Returns:
#       JSON list of rows with anomaly flags and scores
#     """
#     if anomaly_pipeline is None:
#         return func.HttpResponse("Anomaly model not loaded.", status_code=500)

#     try:
#         homeid = get_param(req, "HomeID", None)
#         start = get_param(req, "start", None)
#         end = get_param(req, "end", None)
#         debug = get_param(req, "debug", "false").lower() == "true"

#         # Build query
#         sql = "SELECT c.HomeID, c.Date, c.EnergyConsumption, c.ApplianceType FROM c"
#         where = []
#         parameters = []

#         if homeid:
#             where.append("c.HomeID = @homeid")
#             parameters.append({"name": "@homeid", "value": homeid})
#         if start:
#             where.append("c.Date >= @start")
#             parameters.append({"name": "@start", "value": start})
#         if end:
#             where.append("c.Date <= @end")
#             parameters.append({"name": "@end", "value": end})
#         if where:
#             sql += " WHERE " + " AND ".join(where)

#         items = list(container.query_items(
#             query=sql,
#             parameters=parameters if parameters else None,
#             enable_cross_partition_query=True
#         ))

#         if not items:
#             return func.HttpResponse(json.dumps([]), mimetype="application/json", status_code=200)

#         df = pd.DataFrame(items)
#         df['Date'] = pd.to_datetime(df['Date'], format="%d-%m-%Y")

#         # Aggregate per home per day
#         agg = df.groupby(['HomeID', 'Date']).agg(
#             total_kwh=('EnergyConsumption', 'sum'),
#             unique_appliances=('ApplianceType', 'nunique')
#         ).reset_index()

#         # Fill missing dates per HomeID
#         filled = []
#         for home in agg['HomeID'].unique():
#             sub = agg[agg['HomeID'] == home].set_index('Date')
#             full_range = pd.date_range(start=sub.index.min(), end=sub.index.max(), freq='D')
#             sub = sub.reindex(full_range, fill_value=0)
#             sub['HomeID'] = home
#             sub = sub.reset_index().rename(columns={'index': 'Date'})
#             filled.append(sub)

#         agg = pd.concat(filled).sort_values(['HomeID', 'Date'])

#         # Feature engineering
#         agg['rolling_7_mean'] = agg.groupby('HomeID')['total_kwh'].transform(lambda x: x.rolling(7, min_periods=1).mean())
#         agg['dow'] = agg['Date'].dt.dayofweek

#         feature_cols = ['total_kwh', 'unique_appliances', 'rolling_7_mean', 'dow']
#         X = agg[feature_cols].fillna(0)

#         # Apply model
#         preds = anomaly_pipeline.predict(X)              # -1 = anomaly, 1 = normal
#         scores = anomaly_pipeline.decision_function(X)   # higher = more normal

#         agg['anomaly'] = preds == -1
#         agg['score'] = scores

#         # Optional debug logs
#         if debug:
#             logging.info(f"Total records analyzed: {len(agg)}")
#             logging.info(f"Anomalies detected: {agg['anomaly'].sum()}")
#             logging.info(f"Feature matrix:\n{X.head()}")
#             logging.info(f"Scores:\n{scores[:5]}")

#         logging.info(f"Anomalies detected: {agg['anomaly'].sum()}")
#         logging.info(f"Top anomaly:\n{agg[agg['anomaly'] == True].head()}")
#         # Return results
#         out = agg[['HomeID', 'Date', 'total_kwh', 'unique_appliances', 'rolling_7_mean', 'dow', 'score', 'anomaly']]
#         return func.HttpResponse(body=json.dumps(out.to_dict(orient='records'), default=str),
#                                  mimetype="application/json", status_code=200)

#     except Exception as e:
#         logging.exception("DetectAnomalies error")
#         return func.HttpResponse(f"Error running anomaly detection: {e}", status_code=500)




@app.route(route="DetectAnomalies", auth_level=func.AuthLevel.FUNCTION, methods=["POST", "GET"])
def DetectAnomalies(req: func.HttpRequest) -> func.HttpResponse:
    """
    Query params or POST JSON:
      - HomeID (optional): analyze one home or all homes
      - start (YYYY-MM-DD): start date filter
      - end (YYYY-MM-DD): end date filter
      - debug=true (optional): enables logging of intermediate steps
    Returns:
      JSON list of rows with anomaly flags and scores
    """
    if anomaly_pipeline is None:
        return func.HttpResponse("Anomaly model not loaded.", status_code=500)

    try:
        homeid = get_param(req, "HomeID", None)
        start = get_param(req, "start", None)
        end = get_param(req, "end", None)
        debug = get_param(req, "debug", "false").lower() == "true"

        # Build query (no date filter here — we'll filter manually)
        sql = "SELECT c.HomeID, c.Date, c.EnergyConsumption, c.ApplianceType FROM c"
        where = []
        parameters = []

        if homeid:
            where.append("c.HomeID = @homeid")
            parameters.append({"name": "@homeid", "value": homeid})

        if where:
            sql += " WHERE " + " AND ".join(where)

        items = list(container.query_items(
            query=sql,
            parameters=parameters if parameters else None,
            enable_cross_partition_query=True
        ))

        if not items:
            return func.HttpResponse(json.dumps([]), mimetype="application/json", status_code=200)

        df = pd.DataFrame(items)
        df['Date'] = pd.to_datetime(df['Date'], format="%d-%m-%Y")

        # Manual date filtering
        if start:
            start_dt = pd.to_datetime(start)
            df = df[df['Date'] >= start_dt]
        if end:
            end_dt = pd.to_datetime(end)
            df = df[df['Date'] <= end_dt]

        if df.empty:
            return func.HttpResponse(json.dumps([]), mimetype="application/json", status_code=200)

        # Aggregate per home per day
        agg = df.groupby(['HomeID', 'Date']).agg(
            total_kwh=('EnergyConsumption', 'sum'),
            unique_appliances=('ApplianceType', 'nunique')
        ).reset_index()

        # Fill missing dates per HomeID
        filled = []
        for home in agg['HomeID'].unique():
            sub = agg[agg['HomeID'] == home].set_index('Date')
            full_range = pd.date_range(start=sub.index.min(), end=sub.index.max(), freq='D')
            sub = sub.reindex(full_range, fill_value=0)
            sub['HomeID'] = home
            sub = sub.reset_index().rename(columns={'index': 'Date'})
            filled.append(sub)

        agg = pd.concat(filled).sort_values(['HomeID', 'Date'])

        # Feature engineering
        agg['rolling_7_mean'] = agg.groupby('HomeID')['total_kwh'].transform(lambda x: x.rolling(7, min_periods=1).mean())
        agg['dow'] = agg['Date'].dt.dayofweek

        feature_cols = ['total_kwh', 'unique_appliances', 'rolling_7_mean', 'dow']
        X = agg[feature_cols].fillna(0)

        # Apply model
        preds = anomaly_pipeline.predict(X)              # -1 = anomaly, 1 = normal
        scores = anomaly_pipeline.decision_function(X)   # higher = more normal

        agg['anomaly'] = preds == -1
        agg['score'] = scores

        # Optional debug logs
        if debug:
            logging.info(f"Total records analyzed: {len(agg)}")
            logging.info(f"Anomalies detected: {agg['anomaly'].sum()}")
            logging.info(f"Top anomaly:\n{agg[agg['anomaly'] == True].head()}")
            logging.info(f"Feature matrix:\n{X.head()}")
            logging.info(f"Scores:\n{scores[:5]}")

        # Return results
        out = agg[['HomeID', 'Date', 'total_kwh', 'unique_appliances', 'rolling_7_mean', 'dow', 'score', 'anomaly']]
        return func.HttpResponse(body=json.dumps(out.to_dict(orient='records'), default=str),
                                 mimetype="application/json", status_code=200)

    except Exception as e:
        logging.exception("DetectAnomalies error")
        return func.HttpResponse(f"Error running anomaly detection: {e}", status_code=500)