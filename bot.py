import os
import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from dotenv import load_dotenv
from database import init_db, save_user_selection, get_user_selection, get_all_users

# Загружаем переменные из .env
load_dotenv()
API_URL = 'https://rasp-api.rsue.ru/api/v1/schedule/lessons/'
TOKEN = os.getenv("TOKEN")

# Создаём бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Логирование
logging.basicConfig(level=logging.INFO)

# Создание клавиатуры
def create_schedule_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📅 Расписание на сегодня"))
    keyboard.add(KeyboardButton("📅 Расписание на завтра"))
    keyboard.add(KeyboardButton("📅 Расписание на неделю"))
    keyboard.add(KeyboardButton("⏳ Ближайшее расписание"))
    return keyboard

# Команда /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    selection = await get_user_selection(user_id)
    
    if selection:
        keyboard = create_schedule_keyboard()
        await message.reply(f"Вы уже выбрали: {selection}\nВыберите период для расписания:", reply_markup=keyboard)
    else:
        await message.reply("Привет! Введите название группы или имя преподавателя для получения расписания.")

# Обработчик команд расписания
@dp.message_handler(lambda message: message.text in ["📅 Расписание на сегодня", "📅 Расписание на завтра", "📅 Расписание на неделю", "⏳ Ближайшее расписание"])
async def schedule_by_period(message: types.Message):
    user_id = message.from_user.id
    selection = await get_user_selection(user_id)
    
    if not selection:
        await message.reply("Сначала введите название группы или преподавателя.")
        return

    lessons = await fetch_api_schedule(selection)
    if lessons is None:
        await message.reply("Не удалось получить расписание. Проверьте правильность введенных данных.")
        return

    text = message.text
    if "Расписание на сегодня" in text:
        response_text = filter_schedule_today(lessons)
    elif "Расписание на завтра" in text:
        response_text = filter_schedule_tomorrow(lessons)
    elif "Расписание на неделю" in text:
        response_text = filter_schedule_week(lessons)
    elif "Ближайшее расписание" in text:
        response_text = get_nearest_schedule(lessons)  # ✅ Теперь работает правильно!
    else:
        response_text = "Неверный выбор периода."


    await message.reply(response_text, parse_mode=ParseMode.HTML)

# Обработчик ввода группы или преподавателя
@dp.message_handler()
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    selection = message.text.strip()
    await save_user_selection(user_id, selection)

    keyboard = create_schedule_keyboard()
    await message.reply(f"Группа/преподаватель сохранены: {selection}\nВыберите период для расписания:", reply_markup=keyboard)

# Функция запроса данных с API
async def fetch_api_schedule(name: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{API_URL}{name}') as response:
            if response.status == 200:
                data = await response.json()
                return data
            return None

# Фильтрация расписания
def parse_date(date_str: str):
    return datetime.strptime(date_str, "%d.%m.%Y").date()

def filter_schedule_today(data):
    today = datetime.today().date()
    return get_schedule_for_date(data, today)

def filter_schedule_tomorrow(data):
    tomorrow = datetime.today().date() + timedelta(days=1)
    return get_schedule_for_date(data, tomorrow)

def filter_schedule_week(data):
    today = datetime.today().date()
    week_end = today + timedelta(days=6)
    return get_schedule_for_range(data, today, week_end)

def get_nearest_schedule(data):
    today = datetime.today().date()
    
    # Найдём ближайшую дату с занятиями
    for week in data.get("weeks", []):
        for day in week.get("days", []):
            day_date = parse_date(day["date"])
            if day_date >= today and any(pair["lessons"] for pair in day["pairs"]):
                return get_schedule_for_range(data, day_date, day_date + timedelta(days=6))
    
    return "Ближайших занятий нет."

def get_schedule_for_date(data, date):
    return get_schedule_for_range(data, date, date)

def get_schedule_for_range(data, start_date, end_date):
    schedule = []
    
    for week in data.get("weeks", []):
        for day in week.get("days", []):
            day_date = parse_date(day["date"])
            if start_date <= day_date <= end_date:
                lessons = [
                    f"{pair['startTime']} - {lesson['subject']} ({lesson['kind']['shortName']}), ауд. {lesson['audience']}, {lesson['teacher']['name']}"
                    for pair in day["pairs"] if pair["lessons"]
                    for lesson in pair["lessons"]
                ]
                if lessons:
                    schedule.append(f"📅 {day['name']} ({day['date']}):\n" + "\n".join(lessons))

    return "\n\n".join(schedule) if schedule else "Занятий нет."

# Восстановление данных после перезапуска
async def send_start_message_to_users():
    users = await get_all_users()
    for user_id in users:
        selection = await get_user_selection(user_id)
        if selection:
            keyboard = create_schedule_keyboard()
            try:
                await bot.send_message(user_id, f"Бот перезапущен! Ваш выбор сохранён: {selection}\nВыберите период:", reply_markup=keyboard)
            except:
                continue

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
    loop.run_until_complete(send_start_message_to_users())
    executor.start_polling(dp, skip_updates=True)
