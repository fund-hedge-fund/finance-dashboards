IEX_TOKEN = 'sk_e9c0296cfc7b465ba30082d6bd59c2be'
FMP_TOKEN = 'b02456fa377dffaa8d8bebec36b37f44'

API_URL = 'https://paper-api.alpaca.markets'
API_KEY = 'PK7JMEOSLMPUZNKPOBF9'
API_SECRET = 'ym840rPZSZvbvn5mu0tb5O4VTFoDbBMBuIme2drA'


DB_HOST = '35.222.58.107'
DB_USER = 'hedgefund'
DB_PASS = 'millionin2021'
DB_NAME = 'market_data'

#import streamlit as st
#import plotly.graph_objects as go
#from plotly.subplots import make_subplots
#import os
#import threading
#import time
#import datetime
#import pandas as pd
#import pymysql
#import numpy as np
#udp_con = pymysql.connect(
#    host="db-risk.crtrading.loc",
#    user="AlexI",
#    passwd="nUIEaCSL3jrp8yI4",
#    db="grafana",
#    cursorclass=pymysql.cursors.DictCursor,
#    read_timeout=4,
#    write_timeout=4,
#    connect_timeout=4,
#    autocommit=True)
#query = """
#        select *
#        from Maksim_outright
#        """
#
#copper = pd.read_sql(query, con=udp_con)
#copper.set_index('Date', inplace=True)
#copper.sort_index(inplace=True)
#query = """
#        select *
#        from Maksim_inventory
#        where Product = 'Copper' and Exchange = 'LME'
#        """
#
#inventory = pd.read_sql(query, con=udp_con)
#inventory.set_index('Date', inplace=True)
#inventory.sort_index(inplace=True)
#
#fig = make_subplots(specs=[[{"secondary_y": True}]])
#fig.update_xaxes(showgrid=False)
#fig.update_yaxes(showgrid=False)
#fig.update_layout(legend=dict(
#    yanchor="bottom",
#    y=1,
#    xanchor="left",
#    x=0.01
#))
#fig.update_layout(width=800, height=500)
## fig = inc_data.T['Revenue'].plot.bar(labels=dict(index="Year", value="Billions USD", variable=""))
#fig.add_trace(go.Scatter(x=inventory.index, y=inventory.Qty, showlegend=True, name='Inventory LME'), secondary_y=False)
#fig.add_trace(go.Scatter(x=copper.index, y=copper.Price_S, showlegend=True, name='Copper Price'),
#              secondary_y=True)
#fig.layout.update(xaxis_rangeslider_visible=True)
#
#st.plotly_chart(fig)


import alpaca_trade_api as tradeapi

api = tradeapi.REST(API_KEY, API_SECRET, base_url=API_URL)

# Submit a market order to buy 1 share of Apple at market price
api.submit_order(
    symbol='AAPL',
    qty=1,
    side='buy',
    type='market',
    time_in_force='gtc'
)

# Submit a limit order to attempt to sell 1 share of AMD at a
# particular price ($20.50) when the market opens
api.submit_order(
    symbol='AMD',
    qty=1,
    side='sell',
    type='market'
)

