from pykrx import stock
from datetime import date, timedelta
from indicators import indicators_name # 추후에 indicators_name으로 지표 명을 참고할 생각입니다.
import numpy as np

def get_stock_price(stock_code: str) -> float:
    today = date.today()
    yesterday = today - timedelta(5)
    todayStr = today.strftime("%Y%m%d")
    yesterdayStr = yesterday.strftime("%Y%m%d")
    
    df = stock.get_market_ohlcv(yesterdayStr, todayStr, stock_code)
    print(df)
    return df.iloc[-1]['종가']

def is_buyable_price(ticker_code: str, indic_name: str) -> int:
    #1: buy signal, 0, 유보 -1: Sell signal
    signal = 0
    if indic_name == "RSI":
        signal = evaluate_RSI(ticker_code = ticker_code, n_days = 14) # 임시로 14일동안 보겠습니다. 추후 유동적인 변수로 변경 가능
    
    return signal

'''
RSI를 이용해 매수와 매도, 유보를 판단하는 함수.
RSI : 과거 n일 동안의 전날대비 상승일, 하락일의 비율.
70%이상 -> 과매수, 매도 고려
30%이하 -> 과매도, 매수 고려

parameters
- ticker_code   : str, 종목코드.
- n_days        : int, 금일부터 얼마나 과거까지 실필 것인지 결정.
'''
def evaluate_RSI(ticker_code : str, n_days : int) -> int :
    if n_days <= 0 :
        print(f"유효하지 않은 일수 : {n_days}")
        return 0
    
    today = date.today()
    todayStr = today.strftime("%Y%m%d")
    pastday = today-timedelta(n_days)
    pastdayStr = pastday.strftime("%Y%m%d")
    df = stock.get_market_ohlcv(pastdayStr, todayStr, ticker_code)
    change_per_day_df = df.iloc[:]['등락률']
    change_per_day = change_per_day_df.to_numpy()
    minus = change_per_day[change_per_day < 0] * -1
    plus = change_per_day[change_per_day > 0]
    
    RSI = np.mean(plus) / (np.mean(plus) + np.mean(minus)) * 100
    
    signal = 0
    if RSI >= 70 : signal = 1
    elif RSI <= 30 : signal = -1
    '''
    Welles Wilder는 70과 30을 기준으로 했지만
    70을 넘었다가 다시 하향돌파하면 매도, 30밑으로 빠졌다가 상향돌파하면 매수
    50 상향돌파시 매수, 하향돌파시 매도 등 다양한 응용 전략이 있다.
    '''
    return signal