import streamlit as st
import streamlit.components.v1 as components
import trview
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from iex import IEXStock
import tokens_for_api
import requests
import redis
import json
from datetime import timedelta
import datetime
from financialmodelingprep import FMP
from jobs import populate_holdings
import schedule as sh
from plotly.subplots import make_subplots
import os


def format_number(number):
    return f"{number:,}"


sh.every().monday.at('00:00').do(populate_holdings)
sh.every().tuesday.at('00:00').do(populate_holdings)
sh.every().wednesday.at('00:00').do(populate_holdings)
sh.every().thursday.at('00:00').do(populate_holdings)
sh.every().friday.at('00:00').do(populate_holdings)

dashbrd = st.sidebar.selectbox("Select a Dashboard",
                                     ("Daily Charts", "Candlestick screener", "Stock Fundamentals", "Twitter analysis",
                                      "Reddit trends", "Yahoo Charts"), 2)
st.header(dashbrd)

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
if dashbrd == 'Stock Fundamentals':
    client = redis.from_url(os.environ.get("REDIS_URL"))
    #client = redis.Redis(host='localhost', port=6379, db=0)
    symbol = st.sidebar.text_input('Symbol', value='EPAM')
    stock = IEXStock(tokens_for_api.IEX_TOKEN, symbol)
    fmp = FMP(tokens_for_api.FMP_TOKEN, symbol)
    screen = st.sidebar.selectbox("View", ('Overview', 'Fundamentals', 'News', 'Ownership', 'Technicals'), index=1)
    st.title(screen)
    if screen == 'Overview':
        logo_cache_key = f"{symbol}_logo"
        cached_logo = client.get(logo_cache_key)

        if cached_logo is not None:
            logo = json.loads(cached_logo)
        else:
            logo = stock.get_logo()
            client.set(logo_cache_key, json.dumps(logo))

        company_cache_key = f"{symbol}_company"
        cached_company_info = client.get(company_cache_key)

        if cached_company_info is not None:
            company = json.loads(cached_company_info)
        else:
            company = stock.get_company_info()
            client.set(company_cache_key, json.dumps(company))

        col1, col2 = st.beta_columns([1, 4])

        with col1:
            st.image(logo['url'])

        with col2:
            st.subheader(company['companyName'])
            st.write(company['industry'])
            st.subheader('Description')
            st.write(company['description'])
            st.subheader('CEO')
            st.write(company['CEO'])

    if screen == 'News':
        news_cache_key = f"{symbol}_news"

        news = client.get(news_cache_key)

        if news is not None:
            news = json.loads(news)
        else:
            news = stock.get_company_news()
            client.set(news_cache_key, json.dumps(news))

        for article in news:
            st.subheader(article['headline'])
            dt = datetime.datetime.utcfromtimestamp(article['datetime'] / 1000).isoformat()
            st.write(f"Posted by {article['source']} at {dt}")
            st.write(article['url'])
            st.write(article['summary'])
            st.image(article['image'])

    if screen == 'Fundamentals':

        ratios_cache_key = f"{symbol}_ratios"
        ratios = client.get(ratios_cache_key)
        income_cache_key = f"{symbol}_income"
        income = client.get(income_cache_key)
        balance_cache_key = f'{symbol}_balance'
        balance = client.get(balance_cache_key)
        #income_quarter_cache_key = f'{symbol}_income_quarter'
        #income_quarter = client.get(income_quarter_cache_key)

        if not all((ratios, income, balance)):
            #stats = stock.get_stats()
            ratios = fmp.get_company_ratios()[0]
            income = fmp.get_company_statements('income-statement')[0:5]
            #income_quarter = fmp.get_company_statements('income-statement', 'quarter')[0]
            balance = fmp.get_company_statements('balance-sheet-statement')[0:5]
            client.set(ratios_cache_key, json.dumps(ratios))
            client.set(income_cache_key, json.dumps(income))
            client.set(balance_cache_key, json.dumps(balance))
        else:
            ratios = json.loads(ratios)
            income = json.loads(income)
            balance = json.loads(balance)
            #income_quarter = json.loads(income_quarter)

        st.header('Ratios')

        col1, col2 = st.beta_columns(2)

        with col1:
            st.subheader('P/E')
            st.write(round(ratios['peRatioTTM'], 2))
            st.subheader('PEG Ratio')
            st.write(round(ratios['pegRatioTTM'], 2))
            st.subheader('Price to Sales')
            st.write(round(ratios['priceToSalesRatioTTM'], 2))
            st.subheader('Price to Book')
            st.write(round(ratios['priceBookValueRatioTTM'], 2))
        with col2:
            st.subheader('Revenue')
            st.write(format_number(income[0]['revenue']))
            st.subheader('Operating Income')
            st.write(format_number((income[0]['operatingIncome'])))
            st.subheader('Ebitda')
            st.write(format_number(income[0]['ebitda']))
            st.subheader('Net Income')
            st.write(format_number(income[0]['netIncome']))
        inc_data = pd.DataFrame(index=['Revenue', 'Operating Income', 'EBITDA', 'Net Income'])
        inc_data_table = pd.DataFrame(index=['Revenue', 'Operating Income', 'EBITDA', 'Net Income'])
        income = income[::-1]
        gross_margin = []
        for year in income:
            gross_margin.append(round(100*year['grossProfitRatio'], 2))
            date = datetime.datetime.strptime(year['date'], '%Y-%m-%d').year
            inc_data[date] = [year['revenue'], year['operatingIncome'], year['ebitda'], year['netIncome']]
            inc_data_table[date] = [format_number(year['revenue'] / 1e6), format_number(year['operatingIncome'] / 1e6),
                          format_number(year['ebitda'] / 1e6), format_number(year['netIncome'] / 1e6)]
        st.write('Values in millions USD')
        st.table(inc_data_table)
        pd.options.plotting.backend = "plotly"
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        #fig = inc_data.T['Revenue'].plot.bar(labels=dict(index="Year", value="Billions USD", variable=""))
        fig.add_bar(x=inc_data.columns, y=inc_data.T['Revenue'], showlegend=True, name='Revenue', secondary_y=False)
        fig.add_trace(go.Scatter(x=inc_data.columns, y=gross_margin, showlegend=True, name='Gross Profit Margin (%)'), secondary_y=True)
        st.plotly_chart(fig)
        data = pd.DataFrame(index=['Assets', 'Liabilities', 'Shareholders Equity'])
        balance = balance[::-1]
        data_numerical = pd.DataFrame(index=['Assets', 'Liabilities', 'Shareholders Equity'])
        st.write('Values in millions USD')
        for year in balance:
            date = datetime.datetime.strptime(year['date'], '%Y-%m-%d').year
            data_numerical[date] = [year['totalAssets'], year['totalLiabilities'], year['totalStockholdersEquity']]
            data[date] = [format_number(year['totalAssets']/1e6), format_number(year['totalLiabilities']/1e6), format_number(year['totalStockholdersEquity']/1e6)]
        st.table(data)
        st.area_chart(data_numerical.T)
        #pd.options.plotting.backend = "plotly"
        #fig = data_numerical.T.plot.area()
        #st.plotly_chart(fig)
        fundamentals_cache_key = f"{symbol}_fundamentals"
        fundamentals = client.get(fundamentals_cache_key)
