import requests
import csv
from io import StringIO
import pandas as pd
import datetime
import configs
import alpaca_trade_api as tradeapi
import psycopg2
import psycopg2.extras
import datetime
import logging
from configs import copy_from_stringio
logging.basicConfig(filename='app.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s')


def populate_holdings():
    base_url = 'https://ark-funds.com/wp-content/fundsiteliterature/csv/'
    urls = {'ARKK': base_url + 'ARK_INNOVATION_ETF_ARKK_HOLDINGS.csv',
            'ARKQ': base_url + 'ARK_AUTONOMOUS_TECHNOLOGY_&_ROBOTICS_ETF_ARKQ_HOLDINGS.csv',
            'ARKW': base_url + 'ARK_NEXT_GENERATION_INTERNET_ETF_ARKW_HOLDINGS.csv',
            'ARKG': base_url + 'ARK_GENOMIC_REVOLUTION_MULTISECTOR_ETF_ARKG_HOLDINGS.csv',
            'ARKF': base_url + 'ARK_FINTECH_INNOVATION_ETF_ARKF_HOLDINGS.csv',
            'ARKX': base_url + 'ARK_SPACE_EXPLORATION_&_INNOVATION_ETF_ARKX_HOLDINGS.csv',
            'PRNT': base_url + 'THE_3D_PRINTING_ETF_PRNT_HOLDINGS.csv',
            'IZRL': base_url + 'ARK_ISRAEL_INNOVATIVE_TECHNOLOGY_ETF_IZRL_HOLDINGS.csv'
            }
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0"}
    connection = psycopg2.connect(host=configs.DB_HOST, database=configs.DB_NAME,
                                  user=configs.DB_USER, password=configs.DB_PASS)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("select * from stock_etf where is_etf = TRUE")
    etfs = cursor.fetchall()
    for etf in etfs:
        sbl_etf = etf['symbol']
        r = requests.get(urls[sbl_etf], headers=headers)
        data = StringIO(r.text)
        df = pd.read_csv(data)
        df.dropna(inplace=True)
        df['date'] = df['date'].apply(lambda value: datetime.datetime.strptime(value, '%m/%d/%Y'))
        for idx, row in df.iterrows():
            shares = row['shares']
            weight = row['weight(%)']
            ticker = row['ticker']
            current_date = row['date']
            try:
                cursor.execute("""SELECT * FROM stock_etf WHERE symbol = %s""", (ticker,))
                stock = cursor.fetchone()
            except psycopg2.DataError as de:
                logging.error(de)
                connection.rollback()
                continue
            if stock:
                try:
                    cursor.execute("""
                        INSERT INTO etf_holding (etf_id, holding_id, dt, shares, weight)
                        VALUES (%s, %s, %s, %s, %s)""", (etf['id'], stock['id'], current_date, shares, weight))
                except:
                    continue
        logging.warning(f'Executed successfully for {sbl_etf}')

    connection.commit()
    logging.warning(f'Executed successfully at {datetime.datetime.now()}')


def run_on_initiation():
    api = tradeapi.REST(configs.API_KEY, configs.API_SECRET, base_url=configs.API_URL)
    assets = api.list_assets()
    connection = psycopg2.connect(host=configs.DB_HOST, database=configs.DB_NAME,
                                      user=configs.DB_USER, password=configs.DB_PASS)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    for asset in assets:
        print(f"Inserting stock {asset.name} {asset.symbol}")
        cursor.execute("""
            INSERT INTO stock_etf (name, symbol, exchange, is_etf)
            VALUES (%s, %s, %s, false)
        """, (asset.name, asset.symbol, asset.exchange))
    connection.commit()


def run_on_initiation2():
    connection = psycopg2.connect(host=configs.DB_HOST, database=configs.DB_NAME,
                                  user=configs.DB_USER, password=configs.DB_PASS)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("""
            update stock_etf set is_etf = TRUE
            where symbol in ('ARKK', 'ARKQ', 'PRNT', 'IZRL', 'ARKG', 'ARKF', 'ARKW')
            """)
    connection.commit()

#run_on_initiation()

#run_on_initiation2()

#populate_holdings()


def populate_stock():

    connection = psycopg2.connect(host=configs.DB_HOST, database=configs.DB_NAME, user=configs.DB_USER,
                                  password=configs.DB_PASS)
    api = tradeapi.REST(configs.API_KEY, configs.API_SECRET, base_url=configs.API_URL)
    query = """SELECT * FROM stock WHERE symbol = '%s' ORDER BY dt DESC LIMIT 1"""
    name_with_ticker = pd.read_csv('tickers.csv')
    nw = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:00')
    for idx, row in name_with_ticker.iterrows():
        cursor = connection.cursor()
        sbl = pd.read_sql(query % (row.ticker), con=connection)
        cursor.close()
        st = (sbl['dt'][0] + datetime.timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')
        all_dt = api.get_barset(row.ticker, 'minute', start=st, end=nw).df
        all_dt['volume'] = all_dt['volume'].fillna(0)
        all_dt.dropna(inplace=True)
        all_dt.insert(0, 'symbol', [row.ticker for _ in range(len(all_dt))])
        exchange = sbl['exchange'][0]
        all_dt.insert(6, 'exchange', [exchange for _ in range(len(all_dt))])
        all_dt = all_dt[['symbol', 'open', 'high', 'low', 'close', 'volume', 'exchange']]
        copy_from_stringio(connection, all_dt, 'stock')
        logging.warning(f'Executed successfully for populate DB')
