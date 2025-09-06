import pandas as pd
import json

# read csv
df = pd.read_csv('home_energy_consumption_data.csv')

# data testing 
print(df.head())
print(df.info())

# data cleaning
df = df.fillna('')

json_records = df.to_dict(orient='records')

with open('json_file.json', 'w') as f:
    json.dump(json_records, f, indent=4)

print(f"converted {len(json_records)} records to json")
