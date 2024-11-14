import pandas as pd
from models import *

class UserDB:
    def __init__(self):
        self.users = {}
        return

    def add_user(self, user: User):
        self.users[user.user_id] = user
        return

    def get_user(self, user_id: str) -> User:
        try:
            user = self.users[user_id]
            return user
        except KeyError:
            return None

    def update_user(self, user: User):
        self.users[user.user_id] = user
        return


ticker_df = pd.read_csv("ticker_names.csv")
user_db = UserDB()

def get_stock_code(ticker_name):
    try:
        code = ticker_df.loc[ticker_df["name"] == ticker_name, "code"].values[0]
        if code is not None:
            return code
        else:
            return "999999"
    except IndexError:
        return "999999"

def get_stock_name(ticker_code):
    try:
        code = ticker_df.loc[ticker_df["code"] == ticker_code, "name"].values[0]
        if code is not None:
            return code
        else:
            return "잘못된 이름"
    except IndexError:
        return "잘못된 이름"
