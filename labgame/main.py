#!/usr/bin/env python
# -*-coding: utf-8 -*-
# vim: sw=4 ts=4 expandtab ai
import telebot
import logging
from logging import config as logging_config
from optparse import OptionParser
from optparse import OptionParser
import os.path
import sys
import telebot

DEFAULT_CONFIG = {
    'version': 1.0,
    'formatters': {
        'aardvark': {
            'datefmt': '%Y-%m-%d,%H:%M:%S',
            'format': "%(asctime)15s.%(msecs)03d %(processName)s"
                      " pid:%(process)d tid:%(thread)d %(levelname)s"
                      " %(name)s:%(lineno)d %(message)s"
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'aardvark',
            'stream': 'ext://sys.stdout'
        },
    },
    'loggers': {
        'labgame': {},
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console']
    }
}


def log_init():
    logging_config.dictConfig(DEFAULT_CONFIG)


def get_token():
    parser = OptionParser()

    # Available actions
    parser.add_option("--token-file", "-t", dest="token_file", type="string",
                      default="token.txt",
                      help="Path to telegram token file. Default is %default")

    options, _ = parser.parse_args()
    if not os.path.isfile(options.token_file):
        print("Not found file with token. Exiting.")
        sys.exit(1)

    with open(options.token_file) as tfile:
        token = tfile.read().strip()

    return options, token


def main():
    opts, token = get_token()
    log_init()
    log = logging.getLogger(__name__)

    try:
        bot = telebot.TeleBot(token)
    except Exception as err:
        log.exception('Fail to init connection to Telegram API: %s', err)
        sys.exit(1)

    @bot.message_handler(commands=['start'])
    def start_message(message):
        bot.send_message(message.chat.id, "Привет")
        log.debug('Get cmd start from %s ', message.chat.id)

    @bot.message_handler(commands=['help'])
    def help_message(message):
        bot.send_message(message.chat.id, "Справка")
        log.debug('Get cmd help from %s ', message.chat.id)

    log.info('Start Telegram API polling')
    # Restart on error and not reset storage
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as err:
            log.exception('Error connection to Telegram API: %s', err)


if __name__ == "__main__":
    main()
