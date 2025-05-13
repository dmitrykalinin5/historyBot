import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

token = "ВАШ_ТОКЕН_ТУТ"
bot = telebot.TeleBot(token)

# Папка с отдельными сценами
SCENE_DIR = "story"

user_states = {}

# Загрузка одной сцены из файла
def load_scene(scene_key):
    path = os.path.join(SCENE_DIR, f"{scene_key}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Отправка сцены пользователю
def send_scene(chat_id, scene_key):
    scene = load_scene(scene_key)
    if not scene:
        bot.send_message(chat_id, f"Ошибка: сцена '{scene_key}' не найдена.")
        return

    user_states[chat_id] = scene_key
    text = scene["text"]
    markup = InlineKeyboardMarkup()

    for choice in scene.get("choices", []):
        btn = InlineKeyboardButton(choice["text"], callback_data=choice["next"])
        markup.add(btn)

    bot.send_message(chat_id, text, reply_markup=markup)

# Команда /start
@bot.message_handler(commands=["start"])
def start(message):
    send_scene(message.chat.id, "start")

# Обработка выбора
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    next_scene = call.data
    bot.answer_callback_query(call.id)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    send_scene(call.message.chat.id, next_scene)

bot.polling()
