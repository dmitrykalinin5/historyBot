import time

import requests
import telebot
from datetime import datetime
from requests import ReadTimeout
from telebot.apihelper import ApiTelegramException
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

token = "8178537704:AAEQrPjGPzx6dVjgchrSYlf4ksRDvg5iW0o"
bot = telebot.TeleBot(token)

SCENE_DIR = "story"

user_states = {}
user_karma = {}

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

    karma = user_karma.get(chat_id, 50)
    text = scene["text"]
    markup = InlineKeyboardMarkup()

    choices = scene.get("choices", [])
    for idx, choice in enumerate(choices):
        btn = InlineKeyboardButton(choice["text"], callback_data=str(idx))
        markup.add(btn)

    user_states[chat_id] = {
        "scene": scene_key,
        "choices": choices
    }

    image_path = scene.get("image_path")

    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as photo:
                bot.send_photo(
                    chat_id,
                    photo,
                    caption=f"{text}",
                    reply_markup=markup
                )
        except Exception as e:
            print(f"Ошибка при отправке фото: {e}")
            bot.send_message(chat_id, f"{text}", reply_markup=markup)
    else:
        print(f"Фото не найдено по пути: {image_path}")
        try:
            bot.send_message(chat_id, f"{text}", reply_markup=markup)
        except Exception as e:
            print(f"Ошибка при отправке сцены: {e}")





@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    user_karma[chat_id] = 50
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Информацияℹ️", callback_data="information"))
    markup.add(InlineKeyboardButton("Начать игру🎮", callback_data="startGame"))
    markup.add(InlineKeyboardButton("💡 Предложить идею", callback_data="suggestIdea"))  # Новая кнопка

    with open("startphoto.jpg", "rb") as photo:
        try:
            bot.send_photo(
                chat_id,
                photo,
                caption="Приветствуем тебя в нашем боте, выбери, что хочешь сделать👇:",
                reply_markup=markup
            )
        except Exception as e:
            print(f"Ошибка при отправке фото: {e}")


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):

    chat_id = call.message.chat.id
    data = call.data

    try:
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Ошибка при answer_callback_query: {e}")

    if data == "cancel_idea":
        if user_states.get(chat_id) == "suggesting":
            user_states.pop(chat_id, None)
            bot.send_message(chat_id, "❌ Ввод идеи отменён.")
        else:
            bot.send_message(chat_id, "⚠️ Вы не вводите идею в данный момент.")
        return


    if data == "information":
        bot.send_message(chat_id, "ℹ️ Это сюжетная игра с выбором. Выбирайте варианты и влияйте на карму.")
        return

    if data == "startGame":
        user_karma[chat_id] = 50
        send_scene(chat_id, "startGame")
        return

    if data == "suggestIdea":
        user_states[chat_id] = "suggesting"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("❌ Отменить ввод", callback_data="cancel_idea"))
        bot.send_message(
            chat_id,
            "✍️ Напиши свою идею, и мы обязательно её рассмотрим!\nНе беспокойтесь, всё анонимно.",
            reply_markup=markup
        )
        return

    if data == "end_game":
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

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔁 Начать заново", callback_data="startGame"))

        bot.send_message(chat_id, result_message, reply_markup=markup)
        return

    user_state = user_states.get(chat_id)
    if not user_state:
        bot.send_message(chat_id, "Пожалуйста, начните игру сначала командой /start.")
        return

    scene_key = user_state["scene"]
    choices = user_state["choices"]

    try:
        index = int(data)
        choice = choices[index]
    except (ValueError, IndexError):
        bot.send_message(chat_id, "Недопустимый выбор.")
        return

    next_scene = choice.get("next")
    karma_change = choice.get("karma")
    if karma_change is not None:
        changeKarma(chat_id, karma_change)

    try:
        bot.delete_message(chat_id, call.message.message_id)
    except:
        pass

    if next_scene == "end_game":
        handle_callback(type("Call", (), {"message": call.message, "data": "end_game", "id": call.id})())
    else:
        send_scene(chat_id, next_scene)


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id

    if user_states.get(chat_id) == "suggesting":
        idea_text = message.text.strip()
        username = message.from_user.username or f"id_{chat_id}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with open("ideas.txt", "a", encoding="utf-8") as f:
                f.write(f"[Пользователь: @{username}]\n")
                f.write(f"[Время: {timestamp}]\n")
                f.write(f"Идея: {idea_text}\n")
                f.write("-" * 40 + "\n")
            bot.send_message(chat_id, "✅ Спасибо! Твоя идея сохранена.")
        except Exception as e:
            print(f"Ошибка при записи идеи: {e}")
            bot.send_message(chat_id, "❌ Ошибка при сохранении идеи. Попробуйте позже.")

        user_states.pop(chat_id, None)


bot.remove_webhook()
while True:
    try:
        print("Бот запущен...")
        bot.polling(non_stop=True, interval=0, timeout=20)
    except (ReadTimeout, ConnectionError, requests.exceptions.RequestException, ApiTelegramException) as e:
        print(f"[⚠️ Ошибка соединения]: {e}")
        time.sleep(5)
    except Exception as e:
        print(f"[❌ Критическая ошибка]: {e}")
        time.sleep(5)
