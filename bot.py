import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from aiogram.utils import executor
from dotenv import load_dotenv
from db.database import init_db, save_user_selection, get_user_selection, get_all_users
from handlers.schedule_handler import fetch_and_cache_schedule, get_schedule
from utils.utils import create_schedule_keyboard, rate_limit

# Загружаем переменные из .env
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Создаём бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Логирование
logging.basicConfig(level=logging.INFO)

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
@rate_limit(5)  # Защита от спама (5 сек. между запросами)
async def schedule_by_period(message: types.Message):
    user_id = message.from_user.id
    selection = await get_user_selection(user_id)

    if not selection:
        await message.reply("Сначала введите название группы или преподавателя.")
        return

    schedule_data = await fetch_and_cache_schedule(selection)
    if schedule_data is None:
        await message.reply("Ошибка при получении данных. Проверьте введённые данные.")
        return

    text = message.text
    response_text = get_schedule(schedule_data, text)

    await message.reply(response_text, parse_mode=ParseMode.HTML)

# Обработчик ввода группы или преподавателя
@dp.message_handler()
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    selection = message.text.strip()
    await save_user_selection(user_id, selection)

    keyboard = create_schedule_keyboard()
    await message.reply(f"Группа/преподаватель сохранены: {selection}\nВыберите период для расписания:", reply_markup=keyboard)

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
