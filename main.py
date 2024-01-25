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


def send_message_about_late(late_list, chat_id):
    if late_list:
        text = "{time} îò÷¸ò íå ñäàëè âî âðåìÿ: {users}, íå ïðîïóñòèòå åãî â ñëåäóþùèé ðàç".format(
            users=' '.join(late_list), time=report_type)
    else:
        text = "{time} îò÷¸ò ñäàëè âñå ó÷àñòíèêè, ïðîäîëæàéòå â òîì æå äóõå!".format(time=report_type)
    bot.send_message(chat_id, text)


def send_notify(late_list, chat_id):
    text = "Íàïîìèíàíèå: îñòàëîñü 15 ìèíóò ÷òîáû ñäàòü {time} îò÷¸ò. Íå îòïðàâèëè îò÷¸ò {users}".format(
        users=' '.join(late_list), time=report_type.lower())
    bot.send_message(chat_id, text)


class Data:
    data = db_data.get_db()

    def __str__(self) -> dict:
        return self.data

    def __init__(self):
        self.data = db_data.get_db()

    def new_chat(self, chat_id):
        self.data['chats'][str(chat_id)] = {'users': {}}
        db_data.set_db(self.data)

    def send_report(self, message):
        user_id = str(message.from_user.id)
        chat_id = str(message.chat.id)

        if self.data['chats'][chat_id]['users'].get(user_id) is None:
            self.new_user(message)
        else:
            self.data['chats'][chat_id]['users'][user_id]['is_done'] = True
        db_data.set_db(self.data)

    def new_user(self, message):
        user_id = str(message.from_user.id)
        user_name = str(message.from_user.username)
        chat_id = str(message.chat.id)

        self.data['chats'][chat_id]['users'][user_id] = {'user_name': user_name, 'is_done': True}
        db_data.set_db(self.data)

    def remove_user(self, chat_id, user_id):
        user_id = str(user_id)
        chat_id = str(chat_id)
        self.data['chats'][chat_id]['users'].pop(user_id)

    def check_user(self, chat_id, user_id):
        return self.data['chats'][chat_id]['users'].get(user_id) is not None


class Checker:

    def __init__(self):
        self.late_list = []

    def check_report(self, notify=False):
        for chat in users_data.data['chats']:
            print(chat)
            for user in users_data.data['chats'][chat]['users']:
                if not users_data.data['chats'][chat]['users'][user]['is_done']:
                    self.late_list.append('@' + users_data.data['chats'][chat]['users'][user]['user_name'])
                else:
                    users_data.data['chats'][chat]['users'][user]['is_done'] = False

            if notify:
                send_notify(self.late_list, chat)
            else:
                send_message_about_late(self.late_list, chat)

            self.late_list = []

        db_data.set_db(users_data.data)

        print(self.late_list)

        global report_type

        if report_type == 'Óòðåííèé':
            report_type = 'Âå÷åðíèé'
        else:
            report_type = 'Óòðåííèé'


bot = telebot.TeleBot('6685040611:AAHMXsQ0xLOkWIsZvjNmxtldUUIZU6b9GI0')
my_checker = Checker()
users_data = Data()

morning_time = datetime.time(10, 00, 0)
evening_time = datetime.time(15, 55, 0)

morning_time_notify = morning_time
evening_time_notify = evening_time

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

if 0 <= datetime.datetime.now().hour < morning_time.hour:
    report_type = 'Óòðåííèé'
else:
    report_type = 'Âå÷åðíèé'


# TODO Ñäåëàòü ïðîâåðêó íà íàëè÷èå ÷àòà â áàçå
@bot.message_handler(commands=['start'])
def url(message):
    # markup = types.InlineKeyboardMarkup()
    # btn1 = types.InlineKeyboardButton(text='asd', url='https://habr.com/ru/all/')
    # btn2 = types.InlineKeyboardButton(text='sssss', url='https://habr.com/ru/all/')
    # markup.add(btn1, btn2)
    bot.send_message(message.chat.id, 'Ïðèâåò, ÿ áîò ïîìîùíèê, òåïåðü ÿ áóäó ïîìîãàòü âàì çäåñü \U0001F601')
    Data.data.new_chat(message.chat.id)


@bot.message_handler(commands=['remove'])
def remove_user(message):
    res = re.search(r"\s@\S*\b", message.text)
    if res is None:
        bot.send_message(message.chat.id, 'Íå óäàëîñü íàéòè ó÷àñòíèêà ñ äàííûì òýãîì, ïðîâåðüòå ïðàâèëüíîñòü ââåä¸ííûõ äàííûõ')
    else:
        res = res.group().strip()
        bot.send_message(message.chat.id, res)






@bot.message_handler(content_types='text')
def check_report(message):
    if message.text.startswith('#îó') or message.text.startswith('#îâ'):
        users_data.send_report(message)

    else:
        return False


scheduler = BackgroundScheduler()
scheduler.configure(timezone='Europe/Moscow')
# my_checker.check_report

scheduler.add_job(my_checker.check_report, 'cron',
                  hour=morning_time.hour,
                  minute=morning_time.minute,
                  second=morning_time.second)

scheduler.add_job(my_checker.check_report, 'cron', args=[True],
                  hour=morning_time_notify.hour,
                  minute=morning_time_notify.minute,
                  second=morning_time_notify.second)

scheduler.add_job(my_checker.check_report, 'cron',
                  hour=evening_time.hour,
                  minute=evening_time.minute,
                  second=evening_time.second)

scheduler.add_job(my_checker.check_report, 'cron', args=[True],
                  hour=evening_time_notify.hour,
                  minute=evening_time_notify.minute,
                  second=evening_time_notify.second)

scheduler.start()

bot.polling(none_stop=True, interval=0)
