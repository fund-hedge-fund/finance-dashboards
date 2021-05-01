import json
import random


class populate():
    def __init__(self, width, height, symbol, interval, timezone, theme, style, locale, toolbar_bg, enable_publishing, range, allow_symbol_change, container_id):
        self.width = width
        self.height = height
        self.symbol = symbol
        self.interval = interval
        self.timezone = timezone
        self.theme = theme
        self.style = style
        self.locale = locale
        self.toolbar_bg = toolbar_bg
        self.enable_publishing = enable_publishing
        self.range = range
        self.allow_symbol_change = allow_symbol_change
        self.container_id = container_id


    def populate_json(self):
        return json.dumps(self.__dict__)

    def get_chart(self):
        return str(self.get_header()) + str(self.populate_json()) + self.get_close()

    def get_header(self):
        header = '"<div class="tradingview-widget-container"><div id="' + self.container_id + '"></div><script type="text/javascript">new TradingView.widget('
        return header

    def get_close(self):
        return ');</script>'


def chart():
    with open('config.txt', 'r') as f:
        stocks = f.read().splitlines()
    charts = []
    crt = '<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>'
    for stock in stocks:
        prepor = populate(width=800, height=500, symbol=stock, interval=60,
                                 timezone='Etc/UTC', theme='dark', style='1', locale='en', toolbar_bg='#f1f3f6',
                                 enable_publishing=False, range='YTD', allow_symbol_change=True,
                                 container_id='tradingview_' + str(random.randrange(100000000)))
        crt += prepor.get_chart()
        charts.append(crt)
    return charts, stocks


running_line = """<!-- TradingView Widget BEGIN -->
<div class="tradingview-widget-container">
  <div class="tradingview-widget-container__widget"></div>
  <div class="tradingview-widget-copyright"><a href="https://ru.tradingview.com" rel="noopener" target="_blank"><span class="blue-text"></span></a></div>
  <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
  {
  "symbols": [
    {
      "proName": "FX_IDC:EURUSD",
      "title": "EUR/USD"
    },
    {
      "proName": "BITSTAMP:BTCUSD",
      "title": "BTC/USD"
    },
    {
      "proName": "BITSTAMP:ETHUSD",
      "title": "ETH/USD"
    },
    {
      "description": "ES",
      "proName": "CME_MINI:ES1!"
    },
    {
      "description": "NQ",
      "proName": "CME_MINI:NQ1!"
    },
    {
      "description": "HG",
      "proName": "COMEX:HG1!"
    },
    {
      "description": "GC",
      "proName": "COMEX:GC1!"
    }
  ],
  "showSymbolLogo": true,
  "colorTheme": "dark",
  "isTransparent": false,
  "displayMode": "adaptive",
  "locale": "en"
}
  </script>
</div>
<!-- TradingView Widget END -->"""