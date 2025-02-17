import os
from dotenv import load_dotenv

load_dotenv()
TOKEN=os.getenv("TOKEN")

URL_RINH=os.getenv("URL_RINH")
URL_LESSONS = f"{URL_RINH}/schedule/lessons"