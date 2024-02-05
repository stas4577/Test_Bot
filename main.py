# -*- coding: cp1251 -*-

import telebot
from telebot import types
import json
import requests as req
import db_data
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc
import time
import re
import to_json
from sheets import Sheets
from collections import defaultdict


def send_message_about_late(late_list, chat_id):
    if late_list:
        text = "{time} отчёт не сдали во время: {users}, не пропустите его в следующий раз".format(
            users=' '.join(late_list), time=report_type)
    else:
        text = "{time} отчёт сдали все участники, продолжайте в том же духе!".format(time=report_type)
    bot.send_message(chat_id, text)
    if report_type == 'Вечерний':
        users_data.data['chats'][str(chat_id)]['day'] += 1
        db_data.set_db(users_data.data)


def send_notify(late_list, chat_id):
    if late_list:
        text = "Напоминание: осталось 15 минут чтобы сдать {time} отчёт. Не отправили отчёт {users}".format(
            users=' '.join(late_list), time=report_type.lower())
    else:
        return False
    bot.send_message(chat_id, text)


class Data:
    data = defaultdict(dict, db_data.get_db())

    def new_chat(self, chat_id):
        chat_id = str(chat_id)
        if self.data['chats'].get(chat_id) is None:
            self.data['chats'][chat_id] = {'users': {}}
            self.data['chats'][chat_id]['day'] = 1
            db_data.set_db(self.data)
            return True
        else:
            return False

    def send_report(self, message):
        user_id = str(message.from_user.id)
        chat_id = str(message.chat.id)
        full_name = get_full_name(message)

        # TODO убрать лишний print?
        print('Получен отчёт от пользователя:', full_name)

        if self.data['chats'][chat_id]['users'].get(user_id) is None:
            self.new_user(message)
        else:
            self.data['chats'][chat_id]['users'][user_id]['is_done'] = True
            send_user_update(message, report_type, '1')

        if report_type == 'Вечерний':
            Sheets.new_day(get_date_str(), full_name)

        db_data.set_db(self.data)

    def new_user(self, message):
        user_id = str(message.from_user.id)
        user_name = str(message.from_user.username)
        chat_id = str(message.chat.id)
        list_id = Sheets.add_user(' '.join([message.from_user.first_name, message.from_user.last_name]))
        list_id = list_id['replies'][0]['addSheet']['properties']['sheetId']
        full_name = ' '.join([message.from_user.first_name, message.from_user.last_name])
        self.data['chats'][chat_id]['users'][user_id] = {
            'user_name': user_name,
            'is_done': True,
            'status': [],
            'list_id': str(list_id),
            'full_name': full_name,
        }

        db_data.set_db(self.data)

    def remove_user(self, chat_id, user_id):
        user_id = str(user_id)
        chat_id = str(chat_id)
        self.data['chats'][chat_id]['users'].pop(user_id)

    def check_user(self, chat_id, user_id):
        return self.data['chats'][chat_id]['users'].get(user_id) is not None

    def new_day(self):
        for chat in users_data.data['chats']:
            for user in users_data.data['chats'][chat]['users']:
                Sheets.new_day()


class Checker:

    def __init__(self):
        self.late_list = []

    @staticmethod
    def send_hour_notify():
        text = "Напоминание: остался 1 час на сдачу {time} отчёта, Пожалуйста убедитесь что вы отправили отчёт.".format(
            time=report_time_decl)
        for chat_id in users_data.data['chats']:
            bot.send_message(chat_id, text)

    def check_report(self, notify=False):
        global report_type, report_time_decl

        for chat in users_data.data['chats']:
            print(chat)
            for user in users_data.data['chats'][chat]['users']:

                if not users_data.data['chats'][chat]['users'][user]['is_done']:
                    self.late_list.append('@' + users_data.data['chats'][chat]['users'][user]['user_name'])
                else:
                    if not notify:
                        users_data.data['chats'][chat]['users'][user]['is_done'] = False
                        if report_type == 'Вечерний':
                            users_data.data['chats'][chat]['users'][user]['status'] = []


            if notify:
                send_notify(self.late_list, chat)
            else:
                send_message_about_late(self.late_list, chat)

            self.late_list = []

        db_data.set_db(users_data.data)

        print(self.late_list)

        if not notify:

            if report_type == 'Утренний':
                report_type = 'Вечерний'
                report_time_decl = 'Вечернего'
            else:
                report_type = 'Утренний'
                report_time_decl = 'Утреннего'


bot = telebot.TeleBot('6685040611:AAHMXsQ0xLOkWIsZvjNmxtldUUIZU6b9GI0')
my_checker = Checker()
users_data = Data()

admins_status = ['creator', 'administrator']

morning_time = datetime.time(10, 0, 0)
evening_time = datetime.time(23, 59, 59)

morning_time_notify = morning_time
evening_time_notify = evening_time

# TODO Сделать недельний отчёт

Sheets.connect()

if morning_time_notify.minute < 15:
    morning_time_notify = datetime.time(morning_time_notify.hour - 1, morning_time_notify.minute + 45,
                                        morning_time_notify.second)
else:
    morning_time_notify = datetime.time(morning_time_notify.hour, morning_time_notify.minute - 15,
                                        morning_time_notify.second)

if evening_time_notify.minute < 15:
    evening_time_notify = datetime.time(evening_time_notify.hour - 1, evening_time_notify.minute + 45,
                                        evening_time_notify.second)
else:
    evening_time_notify = datetime.time(evening_time_notify.hour, evening_time_notify.minute - 15,
                                        evening_time_notify.second)

# Установка времени отчёта, вечерний или утренний

report_time_decl = 'Вечернего'
report_type = 'Вечерний'
current_time = str(datetime.datetime.now().hour + 10) + str(datetime.datetime.now().minute + 10) + str(
    datetime.datetime.now().second + 10)
print(current_time)
morning_check_time = str(morning_time.hour + 10) + str(morning_time.minute + 10) + str(morning_time.second + 10)
print(morning_check_time)
if 0 <= int(current_time) < int(morning_check_time):
    report_type = 'Утренний'
    report_time_decl = 'Утреннего'


def is_admin(message):
    user_status = bot.get_chat_member(message.chat.id, message.from_user.id).status
    if user_status in admins_status:
        return True
    else:
        return False


def get_full_name(message):
    full_name = ' '.join([message.from_user.first_name, message.from_user.last_name])
    return full_name


def test():
    pass


def check_message_day(text, chat_id):
    res = re.search(r'#\w\w\d{,3}', text).group()
    res = re.sub(r'#\D*', '', res).strip()
    if res != '' and int(res) == int(users_data.data['chats'][str(chat_id)]['day']):
        return True
    else:
        return False


@bot.message_handler(commands=['start'])
def url(message):
    user_status = is_admin(message)
    if user_status:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Отправить отчёт в ЛС")
        # btn2 = types.InlineKeyboardButton(text='sssss', url='https://habr.com/ru/all/')
        markup.add(btn1)
        res = users_data.new_chat(message.chat.id)
        if res:
            bot.send_message(message.chat.id, 'Привет, я бот помощник, теперь я буду помогать вам здесь \U0001F601')
        else:
            bot.send_message(message.chat.id, 'Я уже работаю в этом чате \U0001F601', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Только администраторы чата могут использовать специальные команды')


@bot.message_handler(commands=['create_table'])
def create_table(message):
    res = Sheets.create_table('Test_table', message.chat.title)
    print(res)


# @bot.message_handler(commands=['create_list'])
# def create_table(message):
#     print(users_data.data['sheet_id'])
#     res = Sheets.create_list('Test_Bot')
#     print(res)


@bot.message_handler(commands=['create_user'])
def add_user(message):
    user_name = ' '.join([message.from_user.first_name, message.from_user.last_name])
    res = Sheets.add_user(user_name)
    print(res)


@bot.message_handler(commands=['test'])
def testim(message):
    date = datetime.datetime.now()
    date = '-'.join([str(date.year), str(date.month), str(date.day)])
    Sheets.new_day(date, [])


def send_user_update(message, report, value):
    full_name = get_full_name(message)
    date = datetime.datetime.now()
    date = '-'.join([str(date.year), str(date.month), str(date.day)])
    Sheets.update_user(full_name, report, value, date)


def get_date_str():
    date = datetime.datetime.now()
    date = '-'.join([str(date.year), str(date.month), str(date.day)])
    return date


print(report_type)


@bot.message_handler(content_types='text')
def check_report(message):
    user_is_admin = is_admin(message)

    # message.chat.title - Имя группы

    # TODO Включить проверку является ли пользователь админом группы
    if not user_is_admin:

    # Проверка существования чата в БД
        if str(message.chat.id) not in users_data.data['chats'].keys():
            bot.send_message(message.chat.id, 'Бот пока не работает в этой группе, для запуска бота напишите /start в чат')
            return False

        if report_type == 'Утренний':
            if message.text.startswith('#оу'):
                if check_message_day(message.text, message.chat.id):
                    users_data.send_report(message)
        elif report_type == 'Вечерний':
            if message.text.startswith('#ов'):
                if check_message_day(message.text, message.chat.id):
                    users_data.send_report(message)

        else:
            return False

    if message.text == 'Отправить отчёт в ЛС' and user_is_admin:
        print('SUCCESS!')


def check_job():
    print('123')


scheduler = BackgroundScheduler(job_defaults={'misfire_grace_time': 15 * 60})
scheduler.configure(timezone='Europe/Moscow')

# my_checker.check_report


# Настройка основных событий

scheduler.add_job(check_job, 'cron',
                  misfire_grace_time=15 * 60, day_of_week="5")

scheduler.add_job(my_checker.check_report, 'cron',
                  misfire_grace_time=15 * 60,
                  hour=morning_time.hour,
                  minute=morning_time.minute,
                  second=morning_time.second)

scheduler.add_job(my_checker.check_report, 'cron', args=[True],
                  misfire_grace_time=15 * 60,
                  hour=morning_time_notify.hour,
                  minute=morning_time_notify.minute,
                  second=morning_time_notify.second)

scheduler.add_job(my_checker.check_report, 'cron',
                  hour=evening_time.hour,
                  minute=evening_time.minute,
                  second=evening_time.second)

scheduler.add_job(my_checker.check_report, 'cron', args=[True],
                  misfire_grace_time=15 * 60,
                  hour=evening_time_notify.hour,
                  minute=evening_time_notify.minute,
                  second=evening_time_notify.second)

# Настройка 1 часового напоминания

scheduler.add_job(my_checker.send_hour_notify, 'cron',
                  misfire_grace_time=15 * 60,
                  hour=morning_time.hour - 1,
                  minute=morning_time.minute,
                  second=morning_time.second)

scheduler.add_job(my_checker.send_hour_notify, 'cron',
                  misfire_grace_time=15 * 60,
                  hour=evening_time.hour - 1,
                  minute=evening_time.minute,
                  second=evening_time.second)

scheduler.start()

bot.polling(none_stop=True, interval=0)
