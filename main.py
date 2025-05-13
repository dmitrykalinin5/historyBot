import telebot
from telebot import types
from telebot.types import InputMediaPhoto

token = "7875328646:AAEnQegv0NAX3qnEs01m-Qbxznnn7zijH8k"
bot = telebot.TeleBot(token)

@bot.message_handler(command=["start"])
def start(message):
    with open("")


bot.polling()