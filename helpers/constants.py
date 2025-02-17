import os
from aiogram import Bot, Dispatcher
from aiogram.types import ParseMode
from aiohttp import ClientTimeout
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
URL_RINH = os.getenv("URL_RINH")
URL_LESSONS = f"{URL_RINH}/schedule/lessons"

BOT = Bot(token=TOKEN, timeout=ClientTimeout(total=120), parse_mode=ParseMode.HTML)
DP_BOT = Dispatcher(BOT)
