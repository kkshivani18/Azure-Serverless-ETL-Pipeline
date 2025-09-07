import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import json

st.title("Home Energy Consumption")

# GetAllEnergyData
API_DATA_ENERGY = "http://localhost:7071/api/GetAllEnergyData"  

response = requests.get(API_DATA_ENERGY)

if response.status_code == 200:
    data = response.json()
    df = pd.DataFrame(data)

    energy_per_appliance = df.groupby("ApplianceType")["EnergyConsumption"].sum().reset_index()

    st.subheader("Total Energy Consumption by Appliance (in kWh)")
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


# GetEnergyByHomeID
st.subheader("Energy Consumption by HomeID")

home_id_input = st.text_input("Enter HomeID (e.g. 430):")

if st.button("Fetch Household Data"):
    if home_id_input:
        API_URL_HOME = f"http://localhost:7071/api/GetEnergyByHomeID?HomeID={home_id_input}"
        response = requests.get(API_URL_HOME)

        if response.status_code == 200:
            data = response.json()
            if data:
                df_home = pd.DataFrame(data)

                energy_per_appliance_home = df_home.groupby("ApplianceType")["EnergyConsumption"].sum().reset_index()

                st.write(f"Energy consumption for HomeID: {home_id_input}")
                fig_home = px.bar(
                    energy_per_appliance_home,
                    x="ApplianceType",
                    y="EnergyConsumption",
                )
                st.plotly_chart(fig_home, use_container_width=True)
                st.dataframe(energy_per_appliance_home)
            else:
                st.warning(f"No records found for HomeID {home_id_input}")
        else:
            st.error("Failed to fetch data for HomeID")

st.subheader("Seasonal Energy Consumption Analysis")

API_URL_SEASON = "http://localhost:7071/api/GetSeasonalConsumption"
response = requests.get(API_URL_SEASON)

if response.status_code == 200:
    data_season = response.json()
    df_season = pd.DataFrame(data_season)

    if not df_season.empty:
        seasonal_consumption = df_season.groupby(["Season", "ApplianceType"])["EnergyConsumption"].sum().reset_index()

        fig_season = px.bar(
            seasonal_consumption,
            x="Season",
            y="EnergyConsumption",
            color="ApplianceType",
            barmode="group",
            title="Energy Consumption per Appliance across Seasons"
        )
        st.plotly_chart(fig_season, use_container_width=True)
        st.dataframe(seasonal_consumption)
    else:
        st.warning("No seasonal consumption data found.")
else:
    st.error("Failed to fetch seasonal consumption data.")


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
