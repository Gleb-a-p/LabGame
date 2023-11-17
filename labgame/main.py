#!/usr/bin/env python3
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

# Типы комнат
# 0 - глухая стена
# 1 - стартовая комната
# 2 - пустая комната
# 3 - выход
# 4,5,6 - пустая комната с надписью на стене

# Коды возврата из функций комнат
# 0 - Игрок погиб в комнате
# 1 - Игрок прошел в комнату
# 2 - Игрок завершил игру

# Направления игрока
# 0 - Север(вверх)
# 1 - Восток(вправо)
# 2 - Юг(вниз)
# 3 - Запад(влево)

MAP = [
      [0, 0, 0, 0, 0, 0],
      [0, 1, 0, 4, 0, 0],
      [0, 2, 2, 2, 5, 0],
      [0, 2, 0, 2, 6, 0],
      [0, 2, 2, 3, 0, 0],
      [0, 0, 0, 0, 0, 0]
      ]

ROOMS = {
        0: "глухая стена",
        1: "пустая комната",
        2: "пустая комната",
        3: "комната-выход",
        4: "пустая комната с надписью на стене",
        5: "пустая комната с надписью на стене",
        6: "пустая комната с надписью на стене"
        }

INSCRIPT_ROOMS = {
                 4: "9 #. ..",
                 5: ".# 1 #.",
                 6: ".# .. 0"
                 }

PLAYER_START_X = 1
PLAYER_START_Y = 1
MAP[PLAYER_START_Y][PLAYER_START_X] = 1
PLAYER_START_DIR = 0
PWD_COMMAND = "pwd/"
PASSWORD = "910"

PLOT_MESSAGE = '''
*СЮЖЕТ*
'''

NEXT_TURN_TEXT = '''
Вы можете:
1. Повернутся влево.
2. Повернутся направо.
'''
# ~ 0. Показать инвентарь.

START_MESSAGE = '''
Привет.
Я текстовая игра-лабиринт в телеграм боте.
Чтобы посмотреть список комманд, введите команду /help.
'''

HELP_MESSAGE = '''
КОМАНДЫ:
 - /start - вывести стартовое сообщение
 - /help - вывести это сообщение
 - /run - начать игру
 - /reset - завершить игру
'''

GOOD_RUN_MESSAGE = "Игра начата."

BAD_RUN_MESSAGE = "Игра уже начата. Перед тем, как начать новую игру, завершите эту командой reset."

GOOD_RESET_MESSAGE = "Игра удалена."

BAD_RESET_MESSAGE = "Игра не найдена. Удалять нечего."

END_GAME_MESSAGE = "Вы вышли из лабиринта за {0} ходов. Игра завершена."

EMPTY_INVENTORY_MESSAGE = "Ваш инвентарь пуст."

TURN_NUMBER_MESSAGE =  "*** ХОД {0} *** "

NEXT_ROOM_MESSAGE = "Перед вами "

UNKNOWN_COMMAND_MESSAGE = "Мы таких команд не знаем, введите одну из предложенного списка."

MOVE_OPTION = "3. Идти вперед."

PWD_OPTION = "pwd. Ввести пароль(чтобы ввести пароль, введите {0}[пароль]). Пароль состоит из 3 различных цифр, которые вы можете найти в глубинах этого подвала."

INSCRIPTION_TEXT = "В комнате, где вы находитесь, на стене вы видите надпись '{0}'."

TRUE_PWD_MESSAGE = "Правильный пароль."

FALSE_PWD_MESSAGE = "Неправильный пароль."


# Класс Карта
class Map:
    # Функция init
    def __init__(self):
        self.map = MAP

    # Получение типа комнаты по координатам
    def get_room_type(self, x, y):
        return self.map[y][x]

    # Получение типа следующей комнаты  по направлению
    def get_type_next_room(self, x, y, direction):
        if direction == 0:
            return self.map[y - 1][x]
        elif direction == 1:
            return self.map[y][x + 1]
        elif direction == 2:
            return self.map[y + 1][x]
        elif direction == 3:
            return self.map[y][x - 1]


# Класс Игрок
class Player:
    # Функция init
    def __init__(self, x, y, direction):
        self.hp = 100
        self.x = x
        self.y = y
        self.direction = direction
        self.inventory = []

    # Поворот по часовой стрелке
    def turn_right(self):
        self.direction = (self.direction + 1) % 4

    # Поворот против часовой стрелки
    def turn_left(self):
        self.direction = self.direction - 1
        if self.direction < 0:
            self.direction = 3

    # Шаг вперед
    def step_forward(self):
        if self.direction == 0:
            self.y -= 1
        elif self.direction == 1:
            self.x += 1
        elif self.direction == 2:
            self.y += 1
        elif self.direction == 3:
            self.x -= 1


# Класс Игра
class Game: 
    # Функция init
    def __init__(self, game_cid, turn_number):
        self.game_cid = game_cid
        self.running = True
        self.map = Map()
        self.player = Player(PLAYER_START_X, PLAYER_START_Y, PLAYER_START_DIR)
        self.turn_number = turn_number

    # Получение номера хода
    def get_num_turn(self):
        return self.turn_number

    # Вывод текущего состояния
    def send_current_state(self, bot):
        next_turn_message = TURN_NUMBER_MESSAGE.format(self.turn_number) + "\n" + NEXT_ROOM_MESSAGE + ROOMS[self.map.get_type_next_room(self.player.x, self.player.y, self.player.direction)] + "\n"
        # ~ bot.send_message(self.game_cid, TURN_NUMBER_MESSAGE.format(self.turn_number))
        # ~ bot.send_message(self.game_cid, NEXT_ROOM_MESSAGE + ROOMS[self.map.get_type_next_room(self.player.x, self.player.y, self.player.direction)])
        if self.map.get_room_type(self.player.x, self.player.y) in INSCRIPT_ROOMS:
            next_turn_message += INSCRIPTION_TEXT.format(INSCRIPT_ROOMS[self.map.get_room_type(self.player.x, self.player.y)]) +"\n"
            # ~ bot.send_message( self.game_cid, INSCRIPTION_TEXT.format(INSCRIPT_ROOMS[self.map.get_room_type(self.player.x, self.player.y)]) )
        next_turn_message += NEXT_TURN_TEXT
        # ~ bot.send_message(self.game_cid, NEXT_TURN_TEXT)
        if self.map.get_type_next_room(self.player.x, self.player.y, self.player.direction) != 0:
            next_turn_message += MOVE_OPTION + "\n"
            # ~ bot.send_message(self.game_cid, MOVE_OPTION)
        if self.map.get_room_type(self.player.x, self.player.y) == 3:
            next_turn_message += PWD_OPTION.format(PWD_COMMAND) + "\n"
            # ~ bot.send_message(self.game_cid, PWD_OPTION.format(PWD_COMMAND))
        bot.send_message(self.game_cid, next_turn_message)
        self.turn_number += 1

    # Выполнение следующего хода
    def next_turn(self, bot, turn):
        running = True
        true_pwd = False
        if turn == "0":
            if self.player.inventory == []:
                bot.send_message(self.game_cid, EMPTY_INVENTORY_MESSAGE)
            else:
                for item in range(len(self.player.inventory)):
                    bot.send_message(self.game_cid, f"{item + 1}. {self.player.inventory[item]}")
        elif turn == "1":
            self.player.turn_left()
        elif turn == "2":
            self.player.turn_right()
        elif turn == "3" and self.map.get_type_next_room(self.player.x, self.player.y, self.player.direction) != 0:
            self.player.step_forward()
        elif turn[0:len(PWD_COMMAND)] == PWD_COMMAND and self.map.get_room_type(self.player.x, self.player.y) == 3:
            if turn[len(PWD_COMMAND):] == PASSWORD:
                true_pwd = True
                bot.send_message(self.game_cid, TRUE_PWD_MESSAGE)
            else:
                bot.send_message(self.game_cid, FALSE_PWD_MESSAGE)
        else:
            bot.send_message(self.game_cid, UNKNOWN_COMMAND_MESSAGE)
        if self.player.hp <= 0 or (self.map.get_room_type(self.player.x, self.player.y) == 3 and true_pwd == True):
            running = False
        return running

    # Определение, продолжается игра или нет
    def is_game_continued(self):
        return self.running


# Класс Игровое Хранилище
class GameStorage: 
    # Функция init
    def __init__(self, log):
        self.games = {}
        self.log = log

    # Проверка, запущена ли игра
    def check_running_game(self, cid):
        return cid in self.games

    # Запуск новой игры
    def start_new_game(self, game_cid, bot):
        self.log.debug(f'Start new game for user {game_cid}')
        self.games[game_cid] = Game(game_cid, 1)
        self.games[game_cid].send_current_state(bot)

    # Игровой цикл
    def in_game_input(self, bot, message, game_cid, game_log):
        game = self.games[game_cid]
        self.log.debug(f'Get input game cmd {message.text} from {game_cid}')
        run = game.next_turn(bot, message.text)
        if not run:
            bot.send_message(game_cid, END_GAME_MESSAGE.format(game.get_num_turn() - 1))
            game_log.debug('Game is ended for chat %s', game_cid)
            self.delete_game(game_cid)
            return
        game.send_current_state(bot)

    # Удаление игры
    def delete_game(self, game_cid):
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
        bot.send_message(cid, BAD_RUN_MESSAGE)
    else:
        try:
            bot.send_message(cid, GOOD_RUN_MESSAGE + PLOT_MESSAGE)
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
            bot.send_message(cid, GOOD_RESET_MESSAGE)
            game_storage.delete_game(cid)
        except Exception as err:
            log.exception(
                "Error in game delete for user %s: %s",
                cid, str(err)
            )
    else:
        bot.send_message(cid, BAD_RESET_MESSAGE)


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
        bot.send_message(message.chat.id, START_MESSAGE)
        log.debug('Get cmd start from %s ', message.chat.id)

    @bot.message_handler(commands=['help'])
    def help_message(message):
        bot.send_message(message.chat.id, HELP_MESSAGE)
        log.debug('Get cmd help from %s ', message.chat.id)

    @bot.message_handler(commands=['run'])
    def run_message(message):
        run_game(message, log, bot, game_storage)

    @bot.message_handler(commands=['reset'])
    def reset_message(message):
        reset_game(message, log, bot, game_storage)

    @bot.message_handler(
        func=lambda msg:
            game_storage.check_running_game(msg.chat.id))
    def get_user_message(message):
        game_storage.in_game_input(bot, message, message.chat.id, log)

    log.info('Start Telegram API polling')
    # Restart on error and not reset storage
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as err:
            log.exception('Error connection to Telegram API: %s', err)


if __name__ == "__main__":
    main()
