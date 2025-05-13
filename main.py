import telebot

token = "7875328646:AAEnQegv0NAX3qnEs01m-Qbxznnn7zijH8k"
bot = telebot.TeleBot(token)

@bot.message_handler(command=["start"])
def start(message):


bot.polling()