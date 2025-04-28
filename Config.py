import os
from dotenv import load_dotenv

load_dotenv()  # Загружает переменные из .env
TOKEN = os.getenv('TOKEN')  # Исправлено с environ на getenv

if not TOKEN:
    print("❌ Ошибка: Токен не найден в .env файле!")
    exit(1)