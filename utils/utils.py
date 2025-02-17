import time
from functools import wraps
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Клавиатура
def create_schedule_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📅 Расписание на сегодня"))
    keyboard.add(KeyboardButton("📅 Расписание на завтра"))
    keyboard.add(KeyboardButton("📅 Расписание на неделю"))
    keyboard.add(KeyboardButton("⏳ Ближайшее расписание"))
    return keyboard

# Защита от спама
user_last_request = {}

def rate_limit(seconds):
    def decorator(func):
        @wraps(func)
        async def wrapper(message, *args, **kwargs):
            user_id = message.from_user.id
            now = time.time()
            if user_id in user_last_request and now - user_last_request[user_id] < seconds:
                return await message.reply("⏳ Подождите перед следующим запросом.")
            user_last_request[user_id] = now
            return await func(message, *args, **kwargs)
        return wrapper
    return decorator
