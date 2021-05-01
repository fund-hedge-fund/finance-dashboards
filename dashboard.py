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
    crts, stocks = trview.chart()
    for i in range(len(crts)):
        st.subheader(stocks[i])
        components.html(crts[i], width=800, height=500)
