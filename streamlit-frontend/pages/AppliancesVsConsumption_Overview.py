import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt

st.header("📊 Appliance vs Energy Consumption")

# GetAllEnergyData
API_DATA_ENERGY = "http://localhost:7071/api/GetAllEnergyData"  

response = requests.get(API_DATA_ENERGY)

if response.status_code == 200:
    data = response.json()
    df = pd.DataFrame(data)

    energy_per_appliance = df.groupby("ApplianceType")["EnergyConsumption"].sum().reset_index()

    # st.subheader("Total Energy Consumption by Appliance (in kWh)")
    fig = px.line(
        energy_per_appliance,
        x="ApplianceType",
        y="EnergyConsumption",
        markers=True,
        title="Total kWh Consumption per Appliance Type"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(energy_per_appliance)

    # KPI cards
    total_energy = df["EnergyConsumption"].sum()
    avg_energy = df["EnergyConsumption"].mean()
    st.metric("Total Energy Consumption", f"{total_energy:.2f} kWh")
    st.metric("Average per Record", f"{avg_energy:.2f} kWh")

    # --- Top 5 Appliances ---
    st.subheader("Top 5 Energy-Draining Appliances")
    top_appliances = df.groupby("ApplianceType")["EnergyConsumption"].sum().nlargest(5).reset_index()
    fig1 = px.bar(top_appliances, x="ApplianceType", y="EnergyConsumption")
    st.plotly_chart(fig1, use_container_width=True)
    
else:
    st.error("Failed to fetch data from API")

