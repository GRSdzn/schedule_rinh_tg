from aiogram import types
from aiogram.types import ParseMode
from db.database import  save_user_selection, get_user_selection, get_all_users
from handlers.schedule_handler import fetch_and_cache_schedule, get_schedule
from helpers.constants import BOT, DP_BOT
from utils.utils import create_schedule_keyboard, rate_limit

# Команда /start
@DP_BOT.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    # user_id = message.from_user.id
    # selection = await get_user_selection(user_id) #выбор пользователя из бд

    await message.reply("Привет! Введите название группы или имя преподавателя для получения расписания.")

# Обработчик команд расписания
@DP_BOT.message_handler(lambda message: message.text in ["📅 Расписание на сегодня", "📅 Расписание на завтра", "📅 Расписание на неделю", "⏳ Ближайшее расписание"])
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
@DP_BOT.message_handler()
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
                await BOT.send_message(user_id, f"Бот перезапущен! Ваш выбор сохранён: {selection}\nВыберите период:", reply_markup=keyboard)
            except:
                continue