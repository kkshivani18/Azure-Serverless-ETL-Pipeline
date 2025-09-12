import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.header("Forecast Consumption and Anomaly Detection")

days = st.slider("Days to forecast", 1, 30, 7)
homeid = st.text_input("Enter HomeID", value="")

API_URL = f"http://localhost:7071/api/Forecast?days={days}" + (f"&HomeID={homeid}" if homeid else "")

if st.button("Get Forecast"):
    resp = requests.get(API_URL, timeout=30)
    if resp.status_code == 200:
        forecast = pd.DataFrame(resp.json())
        if forecast.empty:
            st.warning("No forecast data returned. Check if Cosmos DB has records.")
        else:
            if 'ds' in forecast.columns:
                forecast['ds'] = pd.to_datetime(forecast['ds'])

                # Plot: yhat and interval
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='yhat'))
                fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_upper'], mode='lines', name='upper', line=dict(width=0), showlegend=False))
                fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_lower'], mode='lines', name='lower', line=dict(width=0), fill='tonexty', fillcolor='rgba(0,100,80,0.2)', showlegend=False))
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(forecast)
    
    else:
        st.error("Forecast API error: " + resp.text)

# Anomaly Detection 
homeid = st.text_input("HomeID to analyze")
start = st.date_input("Start date")
end = st.date_input("End date")

if st.button("Detect Anomalies"):
    payload = {"HomeID": homeid} if homeid else {}
    
    params = {}
    if start:
        params['start'] = start.isoformat()
    if end:
        params['end'] = end.isoformat()

    resp = requests.get("http://localhost:7071/api/DetectAnomalies", params={**params, **({'HomeID':homeid} if homeid else {})})
    if resp.status_code == 200:
        anom = pd.DataFrame(resp.json())
        if anom.empty:
            st.info("No data for the requested range.")

        else:
            st.subheader("Anomalies table (rows with anomaly=True)")
            st.dataframe(anom.sort_values(['Date'], ascending=False))

            # plot time series 
            if homeid:
                # fetch the daily series from GetEnergyByHomeID 
                dts = anom[['Date','total_kwh','anomaly']]
                dts['Date'] = pd.to_datetime(dts['Date'])
                fig = px.line(dts, x='Date', y='total_kwh', title=f"Daily kWh for {homeid}")
                anomalies = dts[dts['anomaly'] == True]
                if not anomalies.empty:
                    fig.add_scatter(x=anomalies['Date'], y=anomalies['total_kwh'], mode='markers', marker=dict(color='red', size=8), name='anomaly')
                st.plotly_chart(fig, use_container_width=True)
            
    else:
        st.error("Anomaly API error: " + resp.text)