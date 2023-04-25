# transummary bot is a Telegram Bot that will be able to get audio messages from users and create a gist of the message
# using readily available models from hugging face
import os

# models to use
# - audio transcriber --> Whisper
# - text summarizer --> Hugging Face

# Telegram library to wrap the core functionality
# Flask to expose the bot to Telegram

from transformers import pipeline
import telebot
import ffmpeg
import flask
import logging
import time

API_TOKEN = os.environ.get('TELEGRAM_API_TOKEN')
logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

bot = telebot.TeleBot(API_TOKEN)

app = flask.Flask(__name__)


# Empty webserver index, return nothing, just http 200
@app.route('/', methods=['GET', 'HEAD'])
def index():
    return ''


@app.route("/ping")
def ping():
    return "pong"


# Process webhook calls
@app.route('/webhook', methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)


def transcribe(sample):
    whisper = pipeline('automatic-speech-recognition', model='openai/whisper-medium')
    return whisper(sample, generate_kwargs={"task": "transcribe", "language": "italian"}, chunk_length_s=30)


@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    bot.reply_to(message, "Send me a voice message and I will translate it for you! I work in group as well")


@bot.message_handler(content_types=['audio', 'voice'])
def transummary(message):
    try:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        transcription = transcribe(downloaded_file)['text']
        bot.send_message(message.chat.id, text=transcription, reply_to_message_id=message.id)
    except:
        bot.send_message(message, text=f'Error processing this audio file.')


if __name__ == '__main__':
    if os.environ.get('POOLING', True):
        bot.infinity_polling()
    else:
        app.run(host="0.0.0.0", port=5000, debug=True)
