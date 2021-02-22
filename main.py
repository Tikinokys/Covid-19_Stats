# -*- coding: utf-8 -*-
"""Main module"""
import os

import requests
from bottle import Bottle

import io_utils
from tg_bot_handler import TelegramBot

token, webhook_url = io_utils.read_system_credentials()
app = Bottle(False)
tg_bot = TelegramBot(token=token)
tg_bot.run(app)


@app.get('/test')
def api():
    return "Успешное тестирование"


@app.get("/")
def index():
    return "Успешный запуск"


def run_main():
    print('Запуск на локальной машине')

    telegram_base_url = tg_bot.tgBOT.base_url
    req = requests.get(f'{telegram_base_url}/deleteWebHook')
    req = requests.get(f'{telegram_base_url}/setWebHook?url={webhook_url}/api')
    if req.status_code == requests.codes.ok:
        print('webhook установлен')
        print(req.text)
    else:
        print('webhook не был установлен')

    app.run(host='0.0.0.0', port=5000)


if __name__ == '__main__':
    run_main()
