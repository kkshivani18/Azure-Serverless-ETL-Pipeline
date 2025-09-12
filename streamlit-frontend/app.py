import streamlit as st

# page config
st.set_page_config(
    page_title="⚡ Home Energy Consumption Dashboard",
    page_icon="⚡",
    layout="wide"
)

# header section
# st.markdown("<h1 style='text-align: center; color: #CC9900;'>⚡ Home Energy Consumption Analytics</h1>", unsafe_allow_html=True)
st.markdown("""
<h1 style='text-align: center; color: white; text-shadow: 1px 1px 2px #000;'>⚡ Home Energy Consumption Analytics</h1>
""", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# intro section
st.markdown("""
<div style="font-size: 16px;">
You arrived at <strong>Home Energy Consumption Analytics Dashboard</strong> - a smart platform powered by <strong>Azure Functions</strong> and <strong>CosmosDB</strong> to help you monitor, forecast and optimize household energy usage.
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# highlights
st.markdown("### Features")
cols = st.columns(2)

with cols[0]:
    st.markdown("""
    - 📊 **Overview Dashboard**  
      Visualize total energy usage trends and top-consuming appliances.
      
    - 🏠 **Household Analytics**  
      Dive into energy breakdowns for individual homes.
    """)

with cols[1]:
    st.markdown("""
    - 🤖 **ML Predictions**  
      Forecast future consumption and detect anomalies using machine learning.
    """)

st.markdown("<br>", unsafe_allow_html=True)

# Footer
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center; font-size: 14px;'>Built with ❤️ using Streamlit, Azure and Python</div>", unsafe_allow_html=True)