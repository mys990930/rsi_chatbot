
class StockAlert:
    def __init__(self, stock_code: str):
        self.stock_code = stock_code
        self.indicators = []

    def add_indicator(self, indicator_name: str):
        self.indicators.append(indicator_name)

    def delete_indicator(self, indicator_name: str):
        self.indicators.remove(indicator_name)


class User:
    def __init__(self, telegram_id: int):
        self.user_id = telegram_id
        self.stock_alerts = {} #dict(stock_code: str -> StockAlert)
        self.last_picked_alert_code = ""

    def add_alert(self, alert: StockAlert):
        self.stock_alerts[alert.stock_code] = alert
        self.last_picked_alert_code = alert.stock_code

    def delete_alert(self, stock_code: str, indicator_name: str):
        self.stock_alerts[stock_code].indicators.remove(indicator_name)


