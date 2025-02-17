import aiohttp
import json
from datetime import datetime, timedelta
from db.database import get_schedule_cache, save_schedule_cache
from helpers.constants import URL_LESSONS

async def fetch_and_cache_schedule(name: str):
    """ Получает данные с API или из кэша (если они не устарели). """
    
    # 1️⃣ Проверяем данные в кэше
    cached_data = await get_schedule_cache(name)
    if cached_data:
        print(f"✅ Данные загружены из кэша для {name}:\n{cached_data[:500]}...\n")  # Выводим первые 500 символов
        return json.loads(cached_data)

    print(f"🔄 Кэш устарел. Загружаем данные из API для {name}...")

    # 2️⃣ Запрашиваем новые данные с API
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{URL_LESSONS}/{name}') as response:
            if response.status == 200:
                data = await response.json()
                
                print(f"🌍 Данные получены из API {URL_LESSONS}{name} для {name}:\n{json.dumps(data)[:500]}...\n")  # Выводим первые 500 символов

                await save_schedule_cache(name, json.dumps(data))  # Сохраняем в кэш
                return data

            print(f"❌ Ошибка запроса API: {response.status}")
            return None

def parse_date(date_str: str):
    """ Конвертирует строку даты в объект datetime.date. """
    return datetime.strptime(date_str, "%d.%m.%Y").date()

def get_schedule(data, period):
    """ Возвращает расписание в зависимости от выбранного периода. """
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)

    if "Расписание на сегодня" in period:
        return filter_schedule_by_date(data, today)
    elif "Расписание на завтра" in period:
        return filter_schedule_by_date(data, tomorrow)
    elif "Расписание на неделю" in period:
        return filter_schedule_week(data, today)
    elif "Ближайшее расписание" in period:
        return get_nearest_schedule(data)
    return "Ошибка: Неверный выбор периода."

def get_nearest_schedule(data):
    """ Возвращает расписание начиная с ближайшего дня, где есть занятия. """
    today = datetime.today().date()
    
    # Ищем ближайшую дату с занятиями
    for week in data.get("weeks", []):
        for day in week.get("days", []):
            day_date = parse_date(day["date"])
            if day_date >= today and any(pair["lessons"] for pair in day["pairs"]):
                return filter_schedule_week(data, day_date)

    return "⏳ Ближайших занятий нет."

def filter_schedule_by_date(data, target_date):
    """ Возвращает расписание на конкретную дату. """
    for week in data.get("weeks", []):
        for day in week.get("days", []):
            if parse_date(day["date"]) == target_date:
                return format_lessons(day)
    return f"📅 {target_date.strftime('%d.%m.%Y')} занятий нет."

def filter_schedule_week(data, start_date):
    """ Возвращает расписание на неделю, начиная с указанной даты. """
    week_end = start_date + timedelta(days=6)
    
    schedule = []
    for week in data.get("weeks", []):
        for day in week.get("days", []):
            if start_date <= parse_date(day["date"]) <= week_end:
                schedule.append(format_lessons(day))

    return "\n\n".join(schedule) if schedule else f"📅 С {start_date.strftime('%d.%m.%Y')} по {week_end.strftime('%d.%m.%Y')} занятий нет."

def format_lessons(day):
    """ Форматирует список занятий в удобочитаемый и красивый HTML-шаблон. """
    lessons = []
    for pair in day["pairs"]:
        for lesson in pair["lessons"]:
            lessons.append(
                f"📖  <b>{lesson['subject']}</b> \n"
                f"📝  {lesson['kind']['name']}\n"
                f"🔑  {lesson['audience']}\n"
                f"⏰  {pair['startTime']} - {pair['endTime']}\n"
                f"👨‍🏫  {lesson['teacher']['name']}"
            )
    
    if lessons:
        header = f"———<u>{day['name'].upper()} ({day['date']})</u>———\n\n"
        # separator = "————————————\n"
        content = "\n\n".join(lessons)
        return header + content
    return f"<b>📅 {day['name']} ({day['date']})</b>\nЗанятий нет."