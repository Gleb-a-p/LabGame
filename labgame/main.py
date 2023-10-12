#!/usr/bin/env python
# -*-coding: utf-8 -*-
# vim: sw=4 ts=4 expandtab ai
import telebot
import logging
from logging import config as logging_config
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

NEXT_TURN_TEXT = '''
Вы можете:
    0. Показать инвентарь.
    1. Повернутся влево.
    2. Повернутся направо.
'''


# Типы комнат
# 0 - глухая стена
# 1 - стартовая комната
# 2 - пустая комната
# 3 - выход

# Коды возврата из функций комнат
# 0 - Игрок погиб в комнате
# 1 - Игрок прошел в комнату
# 2 - Игрок завершил игру

# Направления игрока
# 0 - Север(вверх)
# 1 - Восток(вправо)
# 2 - Юг(вниз)
# 3 - Запад(влево)

class Map: # Класс Карта
    def __init__(self): # Функция init
        self.map = [
                    [0, 0, 0, 0, 0],
                    [0, 1, 2, 2, 0],
                    [0, 2, 0, 2, 0],
                    [0, 2, 2, 3, 0],
                    [0, 0, 0, 0, 0]
                   ]

    def get_room_type(self, x, y): # Получение типа комнаты по координатам
        return self.map[y][x]

    def get_type_next_room(self, x, y, direction): # Получение типа следующей комнаты  по направлению
        if direction == 1:
            return self.map[y - 1][x]
        elif direction == 2:
            return self.map[y][x + 1]
        elif direction == 3:
            return self.map[y + 1][x]
        elif direction == 4:
            return self.map[y][x - 1]


class Player: # Класс Игрок
    def __init__(self, x, y, direction): # Функция init
        self.hp = 100
        self.x = x
        self.y = y
        self.direction = direction
        self.inventory = []

    def povorot_right(self): # Поворот по часовой стрелке
        self.direction = (self.direction + 1) % 4

    def povorot_left(self): # Поворот против часовой стрелки
        self.direction = self.direction - 1
        if self.direction < 0:
            self.direction = 3

    def step_forward(self): # Шаг вперед
        if self.direction == 0:
            self.y -= 1
        elif self.direction == 1:
            self.x += 1
        elif self.direction == 2:
            self.y += 1
        elif self.direction == 3:
            self.x -= 1

    def get_koord(self): # Получение координат
        return self.x, self.y

    def get_direction(self): # Получение направления
        return self.direction


class Game: # Класс Игра
    def __init__(self, game_cid): # Функция init
        self.game_cid = game_cid
        self.running = True
        self.map = Map()
        self.player = Player(1, 1, 0)
        self.turn_number = 1

    def get_num_turn(self): # Получение номера хода
        return self.turn_number

    def next_turn(self): # Выполнение следующего хода
        bot.send_message(self.game_cid, f" *** {self.turn_number} *** ")
        bot.send_message(self.game_cid, NEXT_TURN_TEXT)
        if self.map.get_type_next_room(self.player(x), self.player(y), self.player(direction)) != 0:
            bot.send_message(self.game_cid, "    3. Идти вперед")
        turn = int(input("Ваши действия: ")) # ЗАМЕНИТЬ НА ВВОД ДАННЫХ ОТ ТЕЛЕГРАММА
        if turn == 0:
            bot.send_message(self.game_cid, self.player(inventory))
        elif turn == 1:
            self.player.turn_left()
        elif turn == 2:
            self.player.turn_right()
        elif turn == 3 and self.map.get_type_next_room(self.player(x), self.player(y), self.player(direction)) == 2:
            self.player.step_forward()
        if self.player(hp) <= 0:
            running = False
        return running

    def is_game_continued(self): # Определение, продолжается игра или нет
        return self.running


class GameStorage: # Класс Игровое Хранилище
    def __init__(self, log): # Функция init
        self.players = {}
        self.games = {}
        self.log = log

    def check_running_game(self, cid): # Проверка, запущена ли игра
        return cid in self.games

    def start_new_game(self, game_cid, bot): # Запуск новой игры
        self.games[game_cid] = Game(game_cid)
        bot.send_message(game_cid, "Пока в разработке.")

    def delete_game(self, game_cid): # Удаление игры
        del self.games[game_cid]


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


def run_game(message, log, bot, game_storage):
    cid = message.chat.id
    log.debug('Get command run for chat %s', cid)

    if game_storage.check_running_game(cid):
        bot.send_message(cid, "Игра уже начата. Перед тем, как начать новую игру, завершите эту командой reset.")
    else:
        try:
            bot.send_message(cid, "Игра начата.")
            game_storage.start_new_game(cid, bot)
        except Exception as err:
            log.exception(
                "Error in game start for user %s: %s",
                cid, str(err)
            )


def reset_game(message, log, bot, game_storage):
    cid = message.chat.id
    log.debug('Get command reset for chat %s', cid)

    if game_storage.check_running_game(cid):
        try:
            bot.send_message(cid, "Игра удалена.")
            game_storage.delete_game(cid)
        except Exception as err:
            log.exception(
                "Error in game delete for user %s: %s",
                cid, str(err)
            )
    else:
        bot.send_message(cid, "Игра не найдена. Удалять нечего.")


def main():
    opts, token = get_token()
    log_init()
    log = logging.getLogger(__name__)
    game_storage = GameStorage(log=log)

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

    @bot.message_handler(commands=['run'])
    def run_message(message):
        run_game(message, log, bot, game_storage)

    @bot.message_handler(commands=['reset'])
    def reset_message(message):
        reset_game(message, log, bot, game_storage)

    log.info('Start Telegram API polling')
    # Restart on error and not reset storage
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as err:
            log.exception('Error connection to Telegram API: %s', err)


if __name__ == "__main__":
    main()
