import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

token = "8178537704:AAEQrPjGPzx6dVjgchrSYlf4ksRDvg5iW0o"
bot = telebot.TeleBot(token)

# Папка с отдельными сценами
SCENE_DIR = "story"

user_states = {}
user_karma = {}  # <--- теперь карма хранится по chat_id

def changeKarma(chat_id, delta):
    user_karma[chat_id] = user_karma.get(chat_id, 50) + int(delta)

def load_scene(scene_key):
    path = os.path.join(SCENE_DIR, f"{scene_key}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def send_scene(chat_id, scene_key):
    scene = load_scene(scene_key)
    if not scene:
        bot.send_message(chat_id, f"Ошибка: сцена '{scene_key}' не найдена.")
        return

    user_states[chat_id] = scene_key
    karma = user_karma.get(chat_id, 50)
    text = scene["text"]
    markup = InlineKeyboardMarkup()

    for choice in scene.get("choices", []):
        btn = InlineKeyboardButton(choice["text"], callback_data=choice["next"])
        markup.add(btn)

    bot.send_message(chat_id, f"{text}\n\n🧭 Карма: {karma}", reply_markup=markup)

@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    user_karma[chat_id] = 50  # начальное значение
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Информацияℹ️", callback_data="information"))
    markup.add(InlineKeyboardButton("Начать игру🎮", callback_data="startGame"))

    with open("startphoto.jpg", "rb") as photo:
        bot.send_photo(
            chat_id,
            photo,
            caption="Приветствуем тебя в нашем боте, выбери, что хочешь сделать👇:",
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    next_scene = call.data
    bot.answer_callback_query(call.id)

    current_scene_key = user_states.get(chat_id)
    if current_scene_key:
        current_scene = load_scene(current_scene_key)
        if current_scene and "choices" in current_scene:
            for choice in current_scene["choices"]:
                if choice["next"] == next_scene:
                    karma_change = choice.get("karma")
                    if karma_change is not None:
                        changeKarma(chat_id, karma_change)
                    break

    try:
        bot.delete_message(chat_id, call.message.message_id)
    except:
        pass

    send_scene(chat_id, next_scene)

bot.remove_webhook()
bot.polling()
