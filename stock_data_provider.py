from pykrx import stock
from datetime import date, timedelta
import numpy as np
from ta import add_all_ta_features
from ta.utils import dropna
df = None
recent_day = date(1,1,1)

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
        signal = evaluate_RSI(ticker_code = ticker_code)
    elif indic_name == "MACD" :
        signal = evaluate_MACD(ticker_code = ticker_code)
    elif indic_name == "OBV" :
        signal = evaluate_OBV(ticker_code = ticker_code)
    return signal

def get_pykrx_data(ticker_code : str) :
    global recent_day
    today = date.today()
    if recent_day >= today :
        return
    
    pastday = today - timedelta(days = 365)
    pastdayStr = pastday.strftime("%Y%m%d")
    todayStr = today.strftime("%Y%m%d")
    
    data = dropna(stock.get_market_ohlcv(pastdayStr, todayStr, ticker_code))
    global df
    df = add_all_ta_features(data, open="시가", high="고가", low="저가", close="종가", volume="거래량")
    recent_day = today
    print("data update complete")

'''
RSI를 이용해 매수와 매도, 유보를 판단하는 함수.
RSI : 과거 n일 동안의 전날대비 상승일, 하락일의 비율.
70%이상 -> 과매수, 매도 고려
30%이하 -> 과매도, 매수 고려

parameters
- ticker_code   : str, 종목코드.
'''
def evaluate_RSI(ticker_code : str) -> int :
    get_pykrx_data(ticker_code) # 자료 최신화
    
    global df
    RSI = df['momentum_rsi']
    
    signal = 0
    if RSI.iloc[-1] >= 70 : signal = 1
    elif RSI.iloc[-1] <= 30 : signal = -1
    '''
    Welles Wilder는 70과 30을 기준으로 했지만
    70을 넘었다가 다시 하향돌파하면 매도, 30밑으로 빠졌다가 상향돌파하면 매수
    50 상향돌파시 매수, 하향돌파시 매도 등 다양한 응용 전략이 있다.
    '''
    return signal

'''
MACD를 통해 판단
주가가 큰 변화가 없을 때도 MACD는 계속 변화하기 때문에, 사소한 잡음에 대한 대처가 필요함.
MCAD가 시그널을 상향돌파 -> 매수 신호
MACD가 시그널을 하향돌파 -> 매도 신호 

parameters
- ticker_code   : str, 종목 코드
'''
def evaluate_MACD(ticker_code : str) -> int :
    get_pykrx_data(ticker_code) # 자료 최신화
    
    atr = df[-30:]['volatility_atr']
    atr_threshold = atr.mean() # 최근 30일간 변동성 평균
    macd_diff = df['trend_macd_diff']
    macd = df['trend_macd']
    
    signal = 0
    # 오실레이터가 0을 상향돌파(골든크로스), 변동성(상승폭)이 평균을 상회할 경우(잡음 필터링), 매수
    if macd_diff.iloc[-1] > 0 and macd_diff.iloc[-2] < 0 and atr.iloc[-1] >= atr_threshold :
        signal = 1
    # 오실레이터가 0을 하향돌파(데드크로스), 매도
    elif macd_diff.iloc[-1] < 0 and macd_diff.iloc[-2] > 0 and atr.iloc[-1] >= atr_threshold : 
        signal = -1
    # macd가 0을 상향돌파, 매수
    elif macd.iloc[-1] > 0 and macd.iloc[-2] < 0 and atr.iloc[-1] >= atr_threshold :
        signal = 1
    # macd가 0을 하향돌파, 매도
    elif macd.iloc[-1] < 0 and macd.iloc[-2] > 0 and atr.iloc[-1] >= atr_threshold :
        signal = -1
    
    # 이외에도 오실레이터가 전날보다 상승/하락한 경우 등을 조건에 추가할 수 있습니다.
    return signal

'''
OBV를 통해 판단.
거래량 증가 -> 매수 신호(가격 상승 예상)
거래량 하락 -> 매도 신호(가격 하락 예상)

parameters
- ticker_code   : str, 종목 코드
'''
def evaluate_OBV(ticker_code : str) -> int :
    get_pykrx_data(ticker_code) # 자료 최신화
    
    obv = df['volume_obv']
    
    signal = 0
    # 거래량 증가
    if obv.iloc[-1] > obv.iloc[-2] :
        signal = 1
    elif obv.iloc[-1] < obv.iloc[-2] :
        signal = -1
    
    return signal