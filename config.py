import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SECRET_INVITE_CODE = os.getenv("SECRET_INVITE_CODE", "dtm2026Vikulya")

DATABASE_URL = "sqlite+aiosqlite:///./questions.db"