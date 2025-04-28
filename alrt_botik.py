import logging
import telebot
from Config import TOKEN
from datetime import datetime, timedelta
from Parse_lessons import fetch_schedule
from Parser import fetch_replacements
import json
import time
import threading

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Карта дней недели
DAYS_MAP = {
    0: "ПОНЕДЕЛЬНИК",
    1: "ВТОРНИК",
    2: "СРЕДА",
    3: "ЧЕТВЕРГ",
    4: "ПЯТНИЦА",
    5: "СУББОТА",
    6: "ВОСКРЕСЕНЬЕ"
}

# Путь к файлу с подписчиками
USERS_FILE = 'users.json'

# Функция для чтения подписчиков из JSON
def load_users():
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Функция для сохранения подписчиков в JSON
def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as file:
        json.dump(users, file, ensure_ascii=False, indent=4)

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Привет! Я бот для отображения расписания. Вот доступные команды:\n"
                          "📅 /schedule_week — расписание на всю неделю\n"
                          "📆 /schedule — расписание на завтра\n"
                          "🔄 /replacements — замены в расписании\n"
                          "✅ /subscribe — подписаться на ежедневную рассылку\n"
                          "❌ /unsubscribe — отписаться от рассылки")

# Команда /subscribe (подписка на рассылку)
@bot.message_handler(commands=['subscribe'])
def subscribe(message):
    user_id = message.chat.id
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)
        bot.reply_to(message, "✅ Вы подписались на ежедневную рассылку расписания!")
    else:
        bot.reply_to(message, "⚠️ Вы уже подписаны на рассылку.")

# Команда /unsubscribe (отписка от рассылки)
@bot.message_handler(commands=['unsubscribe'])
def unsubscribe(message):
    user_id = message.chat.id
    users = load_users()
    if user_id in users:
        users.remove(user_id)
        save_users(users)
        bot.reply_to(message, "❌ Вы отписались от рассылки.")
    else:
        bot.reply_to(message, "⚠️ Вы не подписаны на рассылку.")

# Команда /schedule_week (полное расписание на неделю)
@bot.message_handler(commands=['schedule_week'])
def schedule_week(message):
    schedule = fetch_schedule()
    bot.reply_to(message, f"📅 Расписание на неделю:\n\n{schedule}" if schedule else "⚠️ Расписание не найдено.")

# Команда /schedule (расписание на завтра)
@bot.message_handler(commands=['schedule'])
def schedule_tomorrow(message):
    tomorrow = (datetime.now().weekday() + 1) % 7
    schedule = get_schedule_for_day(tomorrow)

    if schedule:
        bot.reply_to(message, f"📆 Расписание на завтра ({DAYS_MAP[tomorrow]}):\n\n" + schedule)
    else:
        bot.reply_to(message, f"⚠️ Расписание на завтра ({DAYS_MAP[tomorrow]}) не найдено.")

# Команда /replacements (замены на завтра)
@bot.message_handler(commands=['replacements'])
def replacements(message):
    tomorrow = (datetime.now().weekday() + 1) % 7
    replacement_list = fetch_replacements()

    if replacement_list:
        bot.reply_to(message, f"🔄 Замены на завтра ({DAYS_MAP[tomorrow]}):\n\n" + "\n".join(replacement_list))
    else:
        bot.reply_to(message, "🔄 Нет замен на завтра.")

# Функция получения расписания на конкретный день
def get_schedule_for_day(day):
    if DAYS_MAP[day] == "ВОСКРЕСЕНЬЕ":
        return "Завтра воскресенье — пар нет!"

    full_schedule = fetch_schedule()
    if not full_schedule:
        return None

    blocks = full_schedule.split('---')
    schedule = []
    found = False

    for block in blocks:
        if DAYS_MAP[day] in block:
            found = True
            schedule.append(f"{DAYS_MAP[day]}")
        elif found and any(day in block for day in DAYS_MAP.values()):
            break
        elif found:
            schedule.append(block.strip())

    return "\n".join(schedule) if schedule else None

# Функция для рассылки расписания подписчикам
def send_daily_schedule():
    while True:
        now = datetime.now()
        target_time = now.replace(hour=20, minute=0, second=0, microsecond=0)

        if now > target_time:
            target_time += timedelta(days=1)

        sleep_time = (target_time - now).total_seconds()
        logging.info(f"Ожидание до отправки следующего сообщения: {sleep_time // 60} минут.")
        time.sleep(sleep_time)

        logging.info("Отправка ежедневного расписания...")

        tomorrow = (datetime.now().weekday() + 1) % 7
        schedule = get_schedule_for_day(tomorrow)
        replacements = fetch_replacements()

        message = f"📆 Расписание на завтра ({DAYS_MAP[tomorrow]}):\n\n"
        if schedule:
            message += schedule + "\n\n"
        else:
            message += "⚠️ Расписание не найдено.\n\n"

        if replacements:
            message += f"🔄 Замены на завтра:\n" + "\n".join(replacements)
        else:
            message += "🔄 Нет замен на завтра."

        users = load_users()
        for user_id in users:
            try:
                bot.send_message(user_id, message, parse_mode="HTML")
            except Exception as e:
                logging.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")

# Запуск потока для ежедневной рассылки
threading.Thread(target=send_daily_schedule, daemon=True).start()

# Запуск бота
if __name__ == "__main__":
    bot.polling(none_stop=True)