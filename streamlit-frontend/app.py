import streamlit as st

st.set_page_config(page_title="Home Energy Consumption Dashboard", page_icon="⚡", layout="wide")

st.title("⚡ Home Energy Consumption Analytics")

st.markdown("""
Welcome to the **Home Energy Consumption Analytics Dashboard**.  
This platform leverages **Azure Functions** and **CosmosDB** to process household energy usage data  
and provide **actionable insights** through interactive analytics.
""")

st.markdown("### 🔍 Features of Home Energy Consumption Analytics")
st.markdown("""
- **📊 Overview Dashboard** – See total energy usage trends and top appliances.  
- **🏠 Household Analytics** – Explore energy breakdown for individual households.  
- **🤖 Predictions (ML)** – Forecast future consumption and detect anomalies.  
- **💡 Recommendations** – Get actionable tips for efficient energy usage.  
""")

st.info("👉 Sidebar navigates through different analysis pages.")

