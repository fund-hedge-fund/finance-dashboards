import requests
import csv
from io import StringIO
import pandas as pd
import datetime
import tokens_for_api
import alpaca_trade_api as tradeapi
import psycopg2
import psycopg2.extras
import datetime
import logging
logging.basicConfig(filename='app.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s')


def populate_holdings():
    url = 'https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_INNOVATION_ETF_ARKK_HOLDINGS.csv'
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0"}
    r = requests.get(url, headers=headers)
    data = StringIO(r.text)
    df = pd.read_csv(data)
    df.dropna(inplace=True)
    df['date'] = df['date'].apply(lambda value: datetime.datetime.strptime(value, '%m/%d/%Y'))
    connection = psycopg2.connect(host=tokens_for_api.DB_HOST, database=tokens_for_api.DB_NAME,
                                  user=tokens_for_api.DB_USER, password=tokens_for_api.DB_PASS)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("select * from stock_etf where is_etf = TRUE and symbol = 'ARKK'")
    etfs = cursor.fetchall()

    for idx, row in df.iterrows():
        shares = row['shares']
        weight = row['weight(%)']
        ticker = row['ticker']
        current_date = row['date']
        cursor.execute("""SELECT * FROM stock_etf WHERE symbol = %s""", (ticker,))
        stock = cursor.fetchone()
        if stock:
            cursor.execute("""
                INSERT INTO etf_holding (etf_id, holding_id, dt, shares, weight)
                VALUES (%s, %s, %s, %s, %s)""", (etfs[0]['id'], stock['id'], current_date, shares, weight))

    connection.commit()
    logging.warning(f'Executed successfully at {datetime.datetime.now()}')

#api = tradeapi.REST(tokens_for_api.API_KEY, tokens_for_api.API_SECRET, base_url=tokens_for_api.API_URL)
#assets = api.list_assets()
#cursor.execute("""
#        update stock_etf set is_etf = TRUE
#        where symbol in ('ARKK', 'ARKQ', 'PRNT', 'IZRL', 'ARKG', 'ARKF', 'ARKW')
#        """)
#connection.commit()
#for asset in assets:
#    print(f"Inserting stock {asset.name} {asset.symbol}")
#    cursor.execute("""
#        INSERT INTO stock_etf (name, symbol, exchange, is_etf)
#        VALUES (%s, %s, %s, false)
#    """, (asset.name, asset.symbol, asset.exchange))
#
#connection.commit()
