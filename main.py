from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
import asyncio
import datetime
# API_TOKEN 이용을 위해 .env 사용
from dotenv import load_dotenv
import os

from stock_data_provider import *
from models import User, StockAlert
import db

SELECT, NEW_ALERT, PRINT_ALERTS, MODIFY_ALERT, CANCEL, \
    NEW_ALERT_2, MODIFY_ALERT_2, MODIFY_ALERT_3, MODIFY_ALERT_4 = range(9)
    
# 테스트를 위해 현황 조회 기능을 만듭니다.
SHOW_NOW = 100

reply_keyboard = [
    ["새 종목 알림 등록하기", "등록 종목 알림 정보 출력"],
    ["기존 등록 알림 수정/삭제하기", "취소"],
]
indicator_keyboard = [
    ["RSI", "MACD"],
    ["OBV", "..."],
    ["취소"],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
load_dotenv()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    is_first_user = True
    if db.user_db.get_user(update.effective_sender.id) is not None:
        is_first_user = False

    if is_first_user:
        db.user_db.add_user(User(telegram_id=update.effective_sender.id))
    await update.message.reply_text(
        "지수 알림 챗봇에 오신 것을 환영합니다."
        "시작하려면 아래 키보드에서 원하는 메뉴를 선택해주세요."
        "\n\n1. 새 종목 알림 등록하기"
        "\n\n2. 등록 종목 알림 정보 출력"
        "\n\n3. 기존 등록 알림 수정/삭제하기",
        #"\n\n4. 기존 등록 알림 삭제하기",
        reply_markup=markup,
        )
    print(update.message)
    return SELECT


async def select_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text #메뉴 종류
    #context.user_data["choice"] = text
    if text == "새 종목 알림 등록하기":
        await update.message.reply_text(f"종목 알림을 새로 등록합니다. KOSPI 시장에서 알림을 받길 원하는 종목의 이름을 정확하게 입력해주세요.")
        return NEW_ALERT
    elif text == "등록 종목 알림 정보 출력":
        await update.message.reply_text(f"현재 등록된 종목의 주가 및 지수 정보를 출력합니다. 잠시만 기다려주세요.")
        return await print_alerts(update, context)
    elif text == "기존 등록 알림 수정/삭제하기":
        await update.message.reply_text(f"기존 등록 알림을 수정합니다. 알림을 수정하고자 하는 종목의 이름을 정확하게 입력해주세요.")
        return MODIFY_ALERT
    elif text == "show_now" : # 디버그를 위해 즉시 지표를 조회합니다.
        await update.message.reply_text("종목 정보를 즉시 조회합니다.")
        await print_alerts_now(update, context.bot)
        return SHOW_NOW
    else:
        await update.message.reply_text(f"취소되었습니다. 다시 시작하시려면 /start 를 입력해 시작해주세요.")
        return CANCEL

async def add_new_alert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = db.user_db.get_user(update.effective_sender.id)

    text = update.message.text
    stock_code = db.get_stock_code(text)

    if stock_code == "999999":
        await update.message.reply_text(f"종목 이름이 존재하지 않습니다. 종목 이름을 다시 입력해주세요.")
        return NEW_ALERT
    else:
        user.add_alert(StockAlert(stock_code))
        await update.message.reply_text(f"[{text}] 종목의 알림을 받습니다. \n매매 신호를 받고자 하는 지표를 아래에서 선택해주세요."
                                        "\n현재 제공되는 지표는 다음과 같습니다: "
                                        "\nRSI, MACD, OBV, .......",
                                        reply_markup=ReplyKeyboardMarkup(indicator_keyboard, one_time_keyboard=True), )
        return NEW_ALERT_2

async def add_new_alert_indicator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = db.user_db.get_user(update.effective_sender.id)
    stock_name = db.get_stock_name(user.last_picked_alert_code)
    indicator_name = update.message.text
    try:
        user.stock_alerts[user.last_picked_alert_code].add_indicator(indicator_name)
    except:
        await update.message.reply_text(f"잘못된 지표가 선택되었습니다. 다시 입력해주세요.")
        return NEW_ALERT_2
    finally:
        await update.message.reply_text(f"[{stock_name}] 종목의 [{indicator_name}] 지표가 선택되었습니다. \n지금부터 알림을 수신합니다.")
        return ConversationHandler.END

async def print_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = db.user_db.get_user(update.effective_sender.id)

    text = update.message.text
    await update.message.reply_text(f"현재 등록된 종목별 알림은 다음과 같습니다:")
    for alert in user.stock_alerts.values():
        stock_name = db.get_stock_name(alert.stock_code)
        stock_price = get_stock_price(str(alert.stock_code))
        await update.message.reply_text(f"""[{stock_name}] \n
{', '.join(map(lambda x: str(x), alert.indicators))} \n
[종가] : {stock_price}
""")
    return ConversationHandler.END

async def modify_alert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        ["지표 추가", "지표 삭제"],
    ]
    user = db.user_db.get_user(update.effective_sender.id)
    stock_name = update.message.text
    stock_code = db.get_stock_code(stock_name)
    if stock_code == "999999":
        await update.message.reply_text(f"종목 이름이 등록되어있지 않아 새로 등록합니다. 종목 이름을 다시 입력해주세요.")
        return NEW_ALERT
    else:
        try:
            current_indicators = user.stock_alerts[stock_code].indicators
            user.last_picked_alert_code = stock_code
            await update.message.reply_text(f"현재 [{stock_name}] 종목에 등록되어있는 지표 알림은 다음과 같습니다:\n"
                                            f"{', '.join(map(lambda x: str(x), current_indicators))}")
            await update.message.reply_text(f"원하시는 행동을 아래에서 선택해주세요.",
                                            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True), )
            return MODIFY_ALERT_2
        except KeyError:
            await update.message.reply_text(f"종목 이름이 등록되어있지 않아 새로 등록합니다. 종목 이름을 다시 입력해주세요.")
            return NEW_ALERT

async def modify_alert_add_or_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = db.user_db.get_user(update.effective_sender.id)
    stock_name = db.get_stock_name(user.last_picked_alert_code)
    command = update.message.text
    if command == "지표 추가":
        await update.message.reply_text("\n매매 신호를 받고자 하는 지표를 아래에서 선택해주세요."
                                        "\n현재 제공되는 지표는 다음과 같습니다: "
                                        "\nRSI, MACD, OBV, .......",
                                        reply_markup=ReplyKeyboardMarkup(indicator_keyboard, one_time_keyboard=True), )
        return MODIFY_ALERT_3
    elif command == "지표 삭제":
        await update.message.reply_text("\n매매 신호를 받지 않고자 하는 지표를 아래에서 선택해주세요.",
                                        reply_markup=ReplyKeyboardMarkup(indicator_keyboard, one_time_keyboard=True), )
        return MODIFY_ALERT_4

async def modify_alert_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = db.user_db.get_user(update.effective_sender.id)
    stock_name = db.get_stock_name(user.last_picked_alert_code)
    indicator_name = update.message.text
    try:
        user.stock_alerts[user.last_picked_alert_code].add_indicator(indicator_name)
    except:
        await update.message.reply_text(f"잘못된 지표가 선택되었습니다. 다시 입력해주세요.")
        return MODIFY_ALERT_3
    finally:
        await update.message.reply_text(f"[{stock_name}] 종목의 [{indicator_name}] 지표가 선택되었습니다. \n지금부터 알림을 수신합니다.")
        return ConversationHandler.END

async def modify_alert_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = db.user_db.get_user(update.effective_sender.id)
    stock_name = db.get_stock_name(user.last_picked_alert_code)
    indicator_name = update.message.text
    try:
        user.stock_alerts[user.last_picked_alert_code].delete_indicator(indicator_name)
        await update.message.reply_text(f"더이상 [{stock_name}] 종목의 [{indicator_name}] 지표 알림을 수신하지 않습니다.")
        return ConversationHandler.END
    except:
        await update.message.reply_text(f"잘못된 지표가 선택되었습니다. 다시 입력해주세요.")
        return MODIFY_ALERT_4

async def delete_alert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = db.user_db.get_user(update.effective_sender.id)

    text = update.message.text
    stock_code = db.get_stock_code(text)

    if stock_code == "999999":
        await update.message.reply_text(f"종목 이름이 존재하지 않습니다. 종목 이름을 다시 입력해주세요.")
        return NEW_ALERT
    else:
        user.add_alert(StockAlert(stock_code))
        await update.message.reply_text(f"[{text}] 종목의 알림을 받습니다. \n매매 신호를 받고자 하는 지표를 아래에서 선택해주세요."
                                        "\n현재 제공되는 지표는 다음과 같습니다: "
                                        "\nRSI, MACD, OBV, .......",
                                        reply_markup=ReplyKeyboardMarkup(indicator_keyboard, one_time_keyboard=True), )
        return NEW_ALERT_2

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return ConversationHandler.END

async def send_alerts(bot: Bot, is_market_start):
    for user in db.user_db.users.values():
        if is_market_start:
            await bot.sendMessage(chat_id=user.user_id,
                                  text="장 시작 시 알림을 보내드립니다.")
        else:
            await bot.sendMessage(chat_id=user.user_id,
                                  text="장 마감 시 알림을 보내드립니다.")
        for alert in user.stock_alerts:
            stock_name = db.get_stock_name(alert.stock_code)
            text = f"현재 [{stock_name}]의 주가: {get_stock_price(alert.stock_code)}원"
            for indicator in alert.indicators:
                indic_result = is_buyable_price(alert.stock_code, indicator)
                if indic_result == 1:
                    text += f"\n[{indicator}]지표에 따르면 매수하기 좋은 시점입니다."
                elif indic_result == 0:
                    text += f"\n[{indicator}]지표에 따르면 관망할만한 시점입니다."
                elif indic_result == -1:
                    text += f"\n[{indicator}]지표에 따르면 매도하기 좋은 시점입니다."
            await bot.sendMessage(chat_id=user.user_id, text=text)

async def print_alerts_now(update: Update, bot: Bot) -> int:
    user = db.user_db.get_user(update.effective_sender.id)
    await bot.sendMessage(chat_id=user.user_id, text="현재 등록된 모든 종목의 정보를 출력합니다.")
    for alert in user.stock_alerts.values():
        stock_name = db.get_stock_name(alert.stock_code)
        stock_price = get_stock_price(str(alert.stock_code))
        indicators_info = "\n".join(
            f"[{indicator}] - 매수/매도 신호: {is_buyable_price(str(alert.stock_code), str(indicator))}"
            for indicator in alert.indicators
        )
        text = f"""[{stock_name}] 종목 정보:
[종가]: {stock_price}
지표 정보:
{indicators_info}
"""
        await bot.sendMessage(chat_id=user.user_id, text=text)


async def alarm(bot: Bot):
    while True:
        now = datetime.datetime.now()
        if now.hour == 9 and now.minute == 0 and now.second == 10:
            await send_alerts(bot, True)
        elif now.hour == 15 and now.minute == 30 and now.second == 0:
            await send_alerts(bot, False)
        await asyncio.sleep(1)

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    token = os.environ.get('API_TOKEN')
    bot = Bot(token)
    application = Application.builder().token(token).build()

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT: [
                MessageHandler(
                    filters.Regex(""), select_choice
                ),
            ],
            NEW_ALERT: [
                MessageHandler(
                    filters.Regex(""), add_new_alert
                ),
            ],
            NEW_ALERT_2: [
                MessageHandler(
                    filters.Regex("RSI|MACD|OBV"), add_new_alert_indicator
                ),
            ],
            PRINT_ALERTS: [
                MessageHandler(
                    filters.Regex(""), print_alerts
                )
            ],
            MODIFY_ALERT: [
                MessageHandler(
                    filters.Regex(""), modify_alert
                )
            ],
            MODIFY_ALERT_2: [
                MessageHandler(
                    filters.Regex(""), modify_alert_add_or_delete
                )
            ],
            MODIFY_ALERT_3: [
                MessageHandler(
                    filters.Regex(""), modify_alert_add
                )
            ],
            MODIFY_ALERT_4: [
                MessageHandler(
                    filters.Regex(""), modify_alert_delete
                )
            ],
            CANCEL: [
                MessageHandler(
                    filters.Regex(""), done
                )
            ],
            SHOW_NOW : [
                MessageHandler(
                    filters.Regex(""), print_alerts_now
                )
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^취소"), done)],
    )
    loop = asyncio.get_event_loop()
    application.add_handler(conv_handler)
    # Run the bot until the user presses Ctrl-C
    loop.create_task(alarm(bot))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
