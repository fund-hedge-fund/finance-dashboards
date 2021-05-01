import streamlit as st
import streamlit.components.v1 as components
import trview

st.header('Financial Dashboard')
dashbrd = st.sidebar.selectbox("Select a Dashboard",
                                     ("Daily Charts", "Candlestick screener", "Stock Fundamentals", "Twitter analysis",
                                      "Reddit trends"))
st.subheader(dashbrd)

if dashbrd == 'Daily Charts':
    components.html(trview.running_line, width=800)
    charts, stocks = trview.chart()
    for idx, crt in enumerate(charts):
        st.subheader(stocks[idx])
        components.html(crt, width=800, height=550)

