import os
import json
import joblib
from prophet.serialize import model_from_json

# for testing purpose
script_dir = os.path.dirname(__file__)
local_prophet = os.path.join(script_dir, "prophet_model.json")
local_isoforest = os.path.join(script_dir, "anomaly_isoforest.pkl")

def check_prophet_model(path):
    try:
        with open(path, 'r') as f:
            json_str = f.read()
            model = model_from_json(json_str)
        print("Prophet model loaded successfully.")
        return True
    except Exception as e:
        print(f"Failed to load Prophet model: {e}")
        return False

def check_isoforest_model(path):
    try:
        model = joblib.load(path)
        print("IsolationForest model loaded successfully.")
        return True
    except Exception as e:
        print(f"Failed to load IsolationForest model: {e}")
        return False

if __name__ == "__main__":
    print("Checking model files in:", script_dir)
    prophet_ok = check_prophet_model(local_prophet)
    isoforest_ok = check_isoforest_model(local_isoforest)

    if prophet_ok and isoforest_ok:
        print(" All models are ready to go!")
    else:
        print("One or more models failed to load. Check paths and file integrity.")