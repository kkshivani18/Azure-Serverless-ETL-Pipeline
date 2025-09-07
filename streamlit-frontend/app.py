import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import json


API_URL = "http://localhost:7071/api/GetAllEnergyData"  

response = requests.get(API_URL)

if response.status_code == 200:
    data = response.json()
    df = pd.DataFrame(data)

    energy_per_appliance = df.groupby("ApplianceType")["EnergyConsumption"].sum().reset_index()

    st.title("Home Energy Consumption")
    fig = px.line(
        energy_per_appliance,
        x="ApplianceType",
        y="EnergyConsumption",
        markers=True,
        title="Total kWh Consumption per Appliance Type"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(energy_per_appliance)
else:
    st.error("Failed to fetch data from API")



# with open('try.json') as f:
#     data = json.load(f)

# df = pd.DataFrame(data)

# energy_per_appliance = df.groupby("Appliance Type")["Energy Consumption (kWh)"].sum().reset_index()

# st.title("Home Energy Consumption")
# # st.subheader("Total Energy Consumption by Appliance")

# # plot with plotly
# fig = px.line(
#     energy_per_appliance,
#     x="Appliance Type",
#     y="Energy Consumption (kWh)",
#     markers=True,
#     title="Total kWh Consumption per Appliance Type"
# )

# st.plotly_chart(fig, use_container_width=True)

# st.dataframe(energy_per_appliance)




# # def appliancetype_energy(api_url):
# #     response = requests.get(api_url)
# #     if response.status_code != 200:
# #         st.error("Failed to fetch data from API")
# #         return 

# #     data = response.json()
# #     df = pd.DataFrame(data)



# # home_id = st.text_input("Enter HomeID", "H001")

# # if st.button("Fetch Data"):
# #     url = f"http://localhost:7071/api/GetEnergyDataByID?HomeID={home_id}"
# #     response = requests.get(url)

# #     if response.status_code == 200:
# #         data = response.json()
# #         df = pd.DataFrame(data)
# #         st.write(df)

# #         # e.g.
# #         if "EnergyConsumption" in df.columns and "Date" in df.columns:
# #             df["Date"] = pd.to_datetime(df["Date"])
# #             st.line_chart(df.set_index("Date")["EnergyConsumption"])
# #     else:
# #         st.error("Failed to fetch data from API")
