import streamlit as st
import streamlit.components.v1 as components
import trview
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from prophet import Prophet
from prophet.plot import plot_plotly
from iex import IEXStock
import tokens_for_api
import requests
import redis
import json
import datetime
from financialmodelingprep import FMP
from jobs import populate_holdings
import schedule
from plotly.subplots import make_subplots
import os
import threading
import time


def format_number(number):
    return f"{number:,}"


def job():
    schedule.every().monday.at('11:00').do(populate_holdings)
    schedule.every().tuesday.at('11:00').do(populate_holdings)
    schedule.every().wednesday.at('11:00').do(populate_holdings)
    schedule.every().thursday.at('11:00').do(populate_holdings)
    schedule.every().friday.at('11:00').do(populate_holdings)
    while True:
        schedule.run_pending()
        time.sleep(1)


x = threading.Thread(target=job)
x.start()

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
    symbol = st.sidebar.text_input('Symbol', value='AAPL')
    stock = IEXStock(tokens_for_api.IEX_TOKEN, symbol)
    fmp = FMP(tokens_for_api.FMP_TOKEN, symbol)
    screen = st.sidebar.selectbox("View", ('Overview', 'Fundamentals', 'News', 'Ownership', 'Price Prediction'))
    st.title(screen)
    if screen == 'Price Prediction':
        selected_stock = st.text_input('Select stock for prediction', 'AAPL')
        n_years = st.slider('Years of prediction', 0.5, 4.0)
        period = n_years * 365
        data_load_state = st.text("Load data...")
        data = yf.download(selected_stock, '2015-01-01', datetime.datetime.now().strftime("%Y-%m-%d"))
        data.reset_index(inplace=True)
        data_load_state.text("Loading data...done!")
        st.subheader('Raw data')
        st.write(data.tail())

        # Plot raw data
        def plot_raw_data():
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=data['Date'], y=data['Open'], name="stock_open"))
            fig.add_trace(go.Scatter(x=data['Date'], y=data['Close'], name="stock_close"))
            fig.layout.update(title_text='Time Series data with Rangeslider', xaxis_rangeslider_visible=True)
            st.plotly_chart(fig)
        plot_raw_data()
        # Predict forecast with Prophet.
        df_train = data[['Date', 'Close']]
        df_train = df_train.rename(columns={"Date": "ds", "Close": "y"})
        m = Prophet()
        m.fit(df_train)
        future = m.make_future_dataframe(periods=int(period))
        forecast = m.predict(future)
        # Show and plot forecast
        st.subheader('Forecast data')
        st.write(forecast.tail())
        st.write(f'Forecast plot for {n_years} years')
        fig1 = plot_plotly(m, forecast)
        st.plotly_chart(fig1)
        st.write("Forecast components")
        fig2 = m.plot_components(forecast)
        st.write(fig2)


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
        chart = trview.chart_stock_beg + str([symbol, symbol]) + trview.chart_stock_end
        components.html(chart, width=750, height=500)
        inc_data = pd.DataFrame(index=['Revenue', 'Operating Income', 'EBITDA', 'Net Income'])
        inc_data_table = pd.DataFrame(index=['Revenue', 'Operating Income', 'EBITDA', 'Net Income'])
        income = income[::-1]
        margins = {'gross_margin': [], 'net_margin': []}
        for year in income:
            margins['gross_margin'].append(round(100*year['grossProfitRatio'], 2))
            margins['net_margin'].append(round(100 * year['netIncomeRatio'], 2))
            date = datetime.datetime.strptime(year['date'], '%Y-%m-%d').year
            inc_data[date] = [year['revenue'], year['operatingIncome'], year['ebitda'], year['netIncome']]
            inc_data_table[date] = [format_number(year['revenue'] / 1e6), format_number(year['operatingIncome'] / 1e6),
                          format_number(year['ebitda'] / 1e6), format_number(year['netIncome'] / 1e6)]
        st.write('Values in millions USD')
        st.table(inc_data_table)
        pd.options.plotting.backend = "plotly"
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
        fig.update_layout(legend=dict(
            yanchor="bottom",
            y=1,
            xanchor="left",
            x=0.01
        ))
        fig.update_layout(width=800, height=500)
        #fig = inc_data.T['Revenue'].plot.bar(labels=dict(index="Year", value="Billions USD", variable=""))
        fig.add_bar(x=inc_data.columns, y=inc_data.T['Net Income'], showlegend=True, name='Net Income', secondary_y=False)
        fig.add_trace(go.Scatter(x=inc_data.columns, y=margins['net_margin'], showlegend=True, name='Net Income Margin (%)'), secondary_y=True)
        st.plotly_chart(fig)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
        fig.update_layout(legend=dict(
            yanchor="bottom",
            y=1,
            xanchor="left",
            x=0.01
        ))
        fig.update_layout(width=800, height=500)
        # fig = inc_data.T['Revenue'].plot.bar(labels=dict(index="Year", value="Billions USD", variable=""))
        fig.add_bar(x=inc_data.columns, y=inc_data.T['Revenue'], showlegend=True, name='Revenue', secondary_y=False)
        fig.add_trace(
            go.Scatter(x=inc_data.columns, y=margins['gross_margin'], showlegend=True, name='Gross Profit Margin (%)'),
            secondary_y=True)
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
