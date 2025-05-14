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
        btn = InlineKeyboardButton(choice["text"], callback_data=choice["text"])
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
    data = call.data
    try:
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Ошибка при answer_callback_query: {e}")


    if data == "information":
        bot.send_message(chat_id, "ℹ️ Это сюжетная игра с выбором. Выбирайте варианты и влияйте на карму.")
        return

    if data == "startGame":
        user_states[chat_id] = "startGame"  # первая сцена
        user_karma[chat_id] = 50  # сброс кармы
        send_scene(chat_id, "startGame")
        return

    if data == "Завершить":
        karma = user_karma.get(chat_id, 50)
        if karma <= 25:
            status = "💀 Ты предал Родину."
        elif 50 <= karma <= 75:
            status = "🪖 Ты достойный солдат."
        elif karma > 75:
            status = "🏅 Ты герой своей страны!"
        else:
            status = ""

        result_message = f" Игра завершена.\n Твоя карма: {karma}"
        if status:
            result_message += f"\n\n{status}"

        # 👇 Кнопка "Начать заново"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔁 Начать заново", callback_data="startGame"))

        bot.send_message(chat_id, result_message, reply_markup=markup)
        return

    current_scene_key = user_states.get(chat_id)
    if not current_scene_key:
        bot.send_message(chat_id, "Пожалуйста, начните игру сначала командой /start.")
        return

    current_scene = load_scene(current_scene_key)
    if not current_scene:
        bot.send_message(chat_id, "Ошибка загрузки текущей сцены.")
        return

    next_scene = None
    for choice in current_scene.get("choices", []):
        if choice["text"] == data:
            next_scene = choice["next"]
            karma_change = choice.get("karma")
            if karma_change is not None:
                changeKarma(chat_id, karma_change)
            break

    if next_scene:
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass
        send_scene(chat_id, next_scene)
    else:
        bot.send_message(chat_id, "Недопустимый выбор.")


bot.remove_webhook()
bot.polling()
