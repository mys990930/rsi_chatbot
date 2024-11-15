from pykrx import stock
from datetime import date

def get_stock_price(stock_code: str) -> float:
    today = date.today()
    todayStr = today.strftime("%Y%m%d")
    df = stock.get_market_ohlcv(todayStr, todayStr, stock_code)
    return df.iloc[0]['종가']

def is_buyable_price(ticker_code: str, indic_name: str) -> int:
    #1: buy signal, 0, 유보 -1: Sell signal
    return 0
