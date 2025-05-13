import telebot
from telebot import types
from telebot.types import InputMediaPhoto

token = "8178537704:AAEQrPjGPzx6dVjgchrSYlf4ksRDvg5iW0o"
bot = telebot.TeleBot(token)
bot.remove_webhook()

@bot.message_handler(command=["start"])
def start(message):
    with open("startphoto.jpg") as f1:
        photo = InputMediaPhoto(f1, caption="aaaa")
        bot.send_media_group(message.chat.id, [photo])


bot.polling()