import streamlit as st
import streamlit.components.v1 as components
import trview
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

st.header('Financial Dashboard')
dashbrd = st.sidebar.selectbox("Select a Dashboard",
                                     ("Daily Charts", "Candlestick screener", "Stock Fundamentals", "Twitter analysis",
                                      "Reddit trends", "Yahoo Charts"))
st.subheader(dashbrd)

if dashbrd == 'Daily Charts':
    components.html(trview.running_line, width=800)
    charts, stocks = trview.chart()
    for idx, crt in enumerate(charts):
        st.subheader(stocks[idx])
        components.html(crt, width=800, height=550)

if dashbrd == 'Yahoo Charts':
    ticker_input = st.text_input('Please enter your company ticker:')
    search_button = st.button('Search')
    if search_button:
        hindpetro = yf.Ticker(ticker_input)
        df = hindpetro.history(period="max")
        df = df.reset_index()
        df.rename(columns={"": "Date"})
        for i in ['Open', 'High', 'Close', 'Low']:
            df[i] = df[i].astype('float64')
        fig = go.Figure([go.Scatter(x=df['Date'], y=df['High'])])
        fig.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month",
                         stepmode="backward"),
                    dict(count=6, label="6m", step="month",
                         stepmode="backward"),
                    dict(count=1, label="YTD", step="year",
                         stepmode="todate"),
                    dict(count=1, label="1y", step="year",
                         stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
        st.plotly_chart(fig)