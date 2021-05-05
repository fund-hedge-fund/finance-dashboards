import requests


class FMP:

    def __init__(self, token, symbol):
        self.BASE_URL = 'https://financialmodelingprep.com/api/v3'
        self.token = token
        self.symbol = symbol

    def get_profile(self):
        url = f"{self.BASE_URL}/profile/{self.symbol}?apikey={self.token}"
        r = requests.get(url)
        return r.json()

    def get_company_quote(self):
        url = f"{self.BASE_URL}/quote/{self.symbol}/?apikey={self.token}"
        r = requests.get(url)
        return r.json()

    def get_company_statements(self, statement_type):
        """Statement type should be income-statement, balance-sheet-statement, cash-flow-statement"""
        url = f"{self.BASE_URL}/{statement_type}/{self.symbol}?limit=120&apikey={self.token}"
        r = requests.get(url)
        return r.json()

    def get_company_ratios(self):
        url = f"{self.BASE_URL}/ratios-ttm/{self.symbol}?limit=120&apikey={self.token}"
        r = requests.get(url)
        return r.json()
