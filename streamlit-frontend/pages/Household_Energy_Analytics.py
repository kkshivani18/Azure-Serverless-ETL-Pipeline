import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.header("🏠 Household Energy Analytics")

home_id = st.text_input("Enter HomeID (e.g. 430):")

if st.button("Fetch Data"):
    if home_id:
        API_URL = f"http://localhost:7071/api/GetEnergyByHomeID?HomeID={home_id}"
        response = requests.get(API_URL)

        if response.status_code == 200:
            df = pd.DataFrame(response.json())

            if not df.empty:
                # KPIs
                total_energy = df["EnergyConsumption"].sum()
                avg_energy = df["EnergyConsumption"].mean()
                household_size = df["HouseholdSize"].mean() if "HouseholdSize" in df.columns else "N/A"

                col1, col2 = st.columns(2)
                col1.metric("Total Energy", f"{total_energy:.2f} kWh")
                col2.metric("Avg per Appliance", f"{avg_energy:.2f} kWh")

                # Appliance Breakdown 
                st.subheader("Appliance Breakdown")
                appliance_df = df.groupby("ApplianceType")["EnergyConsumption"].sum().reset_index()
                fig1 = px.pie(appliance_df, names="ApplianceType", values="EnergyConsumption",
                              title=f"Energy by Appliance for Home {home_id}")
                st.plotly_chart(fig1, use_container_width=True)

                # Seasonal Consumption 
                if "Season" in df.columns:
                    st.subheader("Seasonal Energy Usage")
                    season_df = df.groupby("Season")["EnergyConsumption"].sum().reset_index()
                    fig2 = px.bar(season_df, x="Season", y="EnergyConsumption",
                                  title=f"Seasonal Consumption for Home {home_id}")
                    st.plotly_chart(fig2, use_container_width=True)

                # Trend Over Time
                if "Date" in df.columns:
                    st.subheader("Daily Energy Trend")
                    df["Date"] = pd.to_datetime(df["Date"])
                    daily_df = df.groupby("Date")["EnergyConsumption"].sum().reset_index()
                    fig3 = px.line(daily_df, x="Date", y="EnergyConsumption",
                                   title=f"Daily Usage Trend for Home {home_id}", markers=True)
                    st.plotly_chart(fig3, use_container_width=True)

                # home vs Average Household
                API_ALL = "http://localhost:7071/api/GetAllEnergyData"
                resp_all = requests.get(API_ALL)
                if resp_all.status_code == 200:
                    df_all = pd.DataFrame(resp_all.json())
                    avg_all = df_all.groupby("ApplianceType")["EnergyConsumption"].mean().reset_index()
                    compare = appliance_df.merge(avg_all, on="ApplianceType", suffixes=("_Home", "_Avg"))

                    st.subheader(f"Home {home_id} vs Average Household")
                    fig4 = px.bar(compare, x="ApplianceType",
                                  y=["EnergyConsumption_Home", "EnergyConsumption_Avg"],
                                  barmode="group",
                                  title=f"Home {home_id} vs Average Household")
                    st.plotly_chart(fig4, use_container_width=True)

            else:
                st.warning(f"No records found for HomeID {home_id}")
        else:
            st.error("Error fetching household data")
