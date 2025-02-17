import logging
import asyncio
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from db.database import init_db
from handlers.start_handler import send_start_message_to_users
from helpers.constants import DP_BOT

DP_BOT.middleware.setup(LoggingMiddleware())

# Логирование
logging.basicConfig(level=logging.INFO)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
    loop.run_until_complete(send_start_message_to_users())
    executor.start_polling(DP_BOT, skip_updates=True)
