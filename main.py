# -*- coding: utf-8 -*-
import random

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
import emoji
from threading import Thread, Lock



def send_message_about_late(late_list, chat_id):
    if late_list:
        text = "{time} отчёт не отправили вовремя: {users}. {random_phrase} {fine}".format(
            users=' '.join(late_list), time=report_type,
            random_phrase=get_random_phrase(late_message_variants),
            fine=additional_text
        ),
    else:
        text = "{time} отчёт сдали все участники. {random_phrase}".format(
            time=report_type,
            random_phrase=get_random_phrase(phrase_success)
        )
    bot.send_message(chat_id, text, parse_mode='html')
    if report_type == 'Вечерний':
        users_data.data['chats'][str(chat_id)]['day'] += 1
        db_data.set_db(users_data.data)


def send_notify(late_list, chat_id):
    if late_list:
        text = "Напоминание: осталось 15 минут чтобы сдать {time} отчёт. Не отправили отчёт {users}".format(
            users=' '.join(late_list), time=report_type.lower())
    else:
        return False
    bot.send_message(chat_id, text, parse_mode='html')


class Data:
    data = defaultdict(dict, db_data.get_db())

    def new_chat(self, message):
        chat_id = str(message.chat.id)
        if self.data['chats'].get(chat_id) is None:
            self.data['chats'][chat_id] = {'users': {}}
            self.data['chats'][chat_id]['day'] = 1

            sheet_name, sheet_id = Sheets.create_table(message.chat.title)
            self.data['chats'][chat_id]['sheet_id'] = sheet_id
            self.data['chats'][chat_id]['sheet_url'] = sheet_name

            db_data.set_db(self.data)
            return True
        else:
            return False

    def set_chat_sheet(self, sheet_id, chat_id):
        self.data['chats'][chat_id]['sheet_id'] = sheet_id

    def send_report(self, message):
        user_id = str(message.from_user.id)
        chat_id = str(message.chat.id)
        full_name = get_full_name(message)
        is_new_user = False

        # TODO убрать лишний print?
        print('Получен отчёт от пользователя: {name}, время: {time}'.format(
            name=full_name, time=datetime.datetime.now().strftime("%H:%M:%S")
        ))

        if self.data['chats'][chat_id]['users'].get(user_id) is None:
            self.new_user(message)
            is_new_user = True

        else:
            if not self.data['chats'][chat_id]['users'][user_id]['is_done']:
                if report_type == 'Утренний':
                    if not is_new_user:
                        Sheets.change_sheet(users_data.data['chats'][str(message.chat.id)]['sheet_id'])
                        Sheets.new_day(get_date_str(), full_name)
            else:
                return False

            self.data['chats'][chat_id]['users'][user_id]['is_done'] = True
            send_user_update(message, report_type, '1')

        db_data.set_db(self.data)

    def new_user(self, message, chat_id=False, full_date=False):
        user_id = str(message.from_user.id)
        user_name = str(message.from_user.username)
        if chat_id == False:
            chat_id = str(message.chat.id)
        Sheets.change_sheet(users_data.data['chats'][str(chat_id)]['sheet_id'])

        if full_date == False:
            full_date = get_date_str()
        full_name = get_full_name(message)

        list_id = Sheets.add_user(get_full_name(message))
        list_id = list_id['replies'][0]['addSheet']['properties']['sheetId']
        Sheets.update_user(full_name, report_type, '1', full_date)
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


class Checker:

    def __init__(self):
        self.late_list = []

    @staticmethod
    def send_hour_notify():
        text = "Напоминание: остался 1 час на сдачу {time} отчёта, Пожалуйста убедитесь что вы отправили отчёт.".format(
            time=report_time_decl.lower())
        for chat_id in users_data.data['chats']:
            bot.send_message(chat_id, text)

    def check_report(self, notify=False):
        global report_type, report_time_decl

        for chat in users_data.data['chats']:

            for user in users_data.data['chats'][chat]['users']:

                if not users_data.data['chats'][chat]['users'][user]['is_done']:
                    # Если у человека нет user_name
                    if users_data.data['chats'][chat]['users'][user]['user_name'] == "None":
                        self.late_list.append("<a href='tg://user?id={user_id}'>{name}</a>".format(
                            user_id=str(user),
                            name=users_data.data['chats'][chat]['users'][user]['full_name']
                        ))
                    else:
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

        if not notify:

            if report_type == 'Утренний':
                report_type = 'Вечерний'
                report_time_decl = 'Вечернего'
            else:
                report_type = 'Утренний'
                report_time_decl = 'Утреннего'


def get_random_phrase(phrase_list: list):
    return random.choice(phrase_list)


bot = telebot.TeleBot('6685040611:AAHMXsQ0xLOkWIsZvjNmxtldUUIZU6b9GI0')
my_checker = Checker()
users_data = Data()

admins_status = ['creator', 'administrator']

morning_time = datetime.time(10, 0, 0)
evening_time = datetime.time(23, 59, 59)

morning_time_notify = morning_time
evening_time_notify = evening_time

additional_text = " Отправьте на любую благотворительность 250₽, " \
                  "и пришлите сюда в чат скриншот перевода!😉 " \
                  "Согласно принятым всеми вами правилам, " \
                  "за опоздание, даже минутное, мы помогаем " \
                  "другим 😊🌸 "

phrase_success = [
    "Превосходная работа! Ваши отчёты сияют как звёзды в ночном небе! 🌟",
    "Невероятный успех! Ваши отчеты отражают вашу страсть и упорство. 💪",
    "Браво! Каждый ваш отчёт - это шаг на пути к величию. 🚀",
    "Вы несомненно мастера своего дела! Ваши отчеты - пример для подражания. 👏",
    "Удивительно! Ваши отчеты свидетельствуют о вашем таланте и трудолюбии. 👌",
    "Вы превзошли сами себя! Ваши отчеты - это произведения искусства. 🎨",
    "Ваши отчеты как музыка для ушей, полные гармонии и мастерства. 🎶",
    "Каждый ваш отчёт - это очередной шедевр! Продолжайте в том же духе. 🌈",
    "Ваш труд не остался незамеченным. Ваши отчеты - пример высочайшего качества. 🏅",
    "Вы - звезда! Ваши отчеты озаряют путь к успеху. ✨",
    "Прекрасная работа! Ваши отчеты отражают вашу преданность и старание. 🌟",
    "Ваши отчеты - олицетворение профессионализма и внимания к деталям. 💼",
    "Так держать! Ваши отчеты каждый раз превосходят ожидания. 🚀",
    "Вы установили новый стандарт качества с вашими отчетами. Браво! 👍",
    "Каждый ваш отчёт - это путеводная звезда к мечтам и амбициям. 🌠",
    "Ваши отчеты - это праздник для глаз и ума. Великолепно! 🎉",
    "Вы вдохновляете нас всех! Ваши отчеты - пример настойчивости и целеустремленности. 💖",
    "Ваше усердие в отчетах заслуживает самых высоких похвал. Впечатляюще! 👏",
    "Ваши отчеты - как свежий ветер, приносящий новые идеи и перспективы. 🌬️",
    "Вы сияете ярче всех! Ваши отчеты - это воплощение совершенства. 🌟",
    "Ваши отчеты озаряют путь к успеху, как солнце освещает утро. ☀️",
    "Такое мастерство! Ваши отчеты - пример уникальности и креативности. 🎨",
    "Вы - истинные вдохновители! Ваши отчеты показывают, на что вы способны. 🌈",
    "Ваши отчеты - это мост в будущее полное достижений и успехов. 🌉",
    "Вы доказали, что ничего невозможного нет. Ваши отчеты - это подтверждение. 💪",
    "Ваши отчеты - это песня успеха, наполненная гармонией и мелодией. 🎵",
    "Ваши отчеты - это легенда о вашем труде и старании. Легендарно! 🏆",
    "Такое внимание к деталям! Ваши отчеты - пример исключительной работы. 🔍",
    "Вы - источник вдохновения! Ваши отчеты - это воплощение вашего духа. 💫",
    "Ваши отчеты - как маяк, освещающий путь к цели. Блестяще! 🚩",
    "Ваши отчеты - это путешествие в мир качества и совершенства. 🗺️",
    "Ваши отчеты - это поэзия успеха, написанная вашими руками. 📜",
    "Ваши отчеты - это мозаика успеха, собранная из мелких деталей мастерства. 🎭",
    "Вы - чемпион в создании отчетов, каждый из которых - триумф усердия! 🏆",
    "Ваши отчеты - как музыкальная симфония, в которой каждая нота на своем месте. 🎼",
    "Вы разгадали код успеха! Ваши отчеты - это шифр совершенства. 🗝️",
    "Каждый ваш отчет - как капля в океане ваших достижений. Невероятно! 💧",
    "Ваши отчеты - это северное сияние в мире работы. Завораживающе! 🌌",
    "Вы воплотили ваши мечты в каждом отчете. Ваши усилия не зря! 💭",
    "Вы взлетели к вершинам мастерства в ваших отчетах. Потрясающе! 🚀",
    "Ваши отчеты - это оазис в пустыне повседневности. Восхитительно! 🌴",
    "Вы пишете историю успеха с каждым отчетом. Вдохновляюще! 📚",
    "Ваши отчеты - как зеркало вашей души, отражающее ваши усилия. 🗺️",
    "Каждый ваш отчет - это кирпичик в стене вашего профессионального роста. 🧱",
    "Ваши отчеты - как вспышка света в темноте, освещающая путь к успеху. 💡",
    "Вы - маэстро в мире отчетов. Ваше мастерство поражает! 🎻",
    "Каждый ваш отчет - это отголосок вашего неутомимого стремления к совершенству. 🌟",
    "Вы - алхимики успеха, превращающие каждый отчет в золото. 🧪",
    "Ваши отчеты - это танец слов и цифр, создающий гармонию успеха. 💃",
    "Ваши отчеты - это гимн вашему упорству и таланту. Непревзойденно! 🎵",
    "Вы рисуете картину своего успеха через каждый отчет. Вдохновляете! 🖼️",
    "Ваши отчеты - как кулинарное произведение, приготовленное с любовью и мастерством. 🍳",
    "Каждый ваш отчет - это шаг к вершине ваших возможностей. Восхищаюсь вами! 🏔️",
    "Ваши отчеты - как рассвет нового дня, полного новых возможностей. 🌅",
    "Вы - мастер слов и анализа. Ваши отчеты - это ваше искусство. 📖",
    "Каждый ваш отчет - это волна инноваций и прогресса. Отлично! 🌊",
    "Ваши отчеты - это путеводный свет в мире постоянного развития. 🔦",
    "Вы - архитектор вашего успеха, а ваши отчеты - это его фундамент. 🏗️",
    "Ваши отчеты - это сад ваших достижений, где каждый цветок - это ваш труд. 🌺",
    "Вы вдыхаете жизнь в каждый отчет, делая его живым и динамичным. 🍃",
    "Ваши отчеты - как радуга после дождя, полная надежды и света. 🌈",
    "Вы - рыцари на полях отчетности, сражающиеся за качество и точность. 🛡️",
    "Каждый ваш отчет - это звездопад ваших достижений, освещающий путь другим. ✨"
]

late_message_variants = [
    "Вы сегодня, наверняка, были так заняты покорением мира своей красотой, что забыли сдать  "
    "отчёт. Cоизвольте внести так же свой вклад в помощь нуждающимся в Вашем внимании 💖",
    "Ваша занятость сегодня, без сомнения, была направлена на великие дела, но не забывайте о маленьких "
    "победах в виде сданных отчётов 🌟",
    "Похоже, сегодня у вас был день полный чудес и волшебства, но не забывайте добавить к ним отчёт ✨",
    "Ваши грандиозные планы на сегодня, видимо, отняли все время. Но не упускайте момент поделиться с нами "
    "своими "
    "успехами в отчёте 🚀",
    "Ваше мастерство управления временем сегодня, кажется, подвело. Не забывайте найти минутку для отчёта 😊",
    "Сегодня вы, наверное, творили чудеса, но не забывайте о магии отчёта. Может, ваши чудеса принесут "
    "радость "
    "не только вам, но и кому-то еще? 🌟✨",
    "Вы, как волшебник, сегодня были заняты созданием чудес, но помните: каждый отчёт – это еще одно "
    "волшебство. И не забудьте о маленьком вкладе в большое дело! 🎩🌈",
    "Ваши героические свершения сегодня, вероятно, не оставили времени для отчёта. Но помните: каждый "
    "вклад в "
    "отчёт - это шанс сделать мир лучше! 🚀💫",
    "Похоже, сегодня вы были заняты покорением мира, но не забывайте о маленьких шагах, таких как отчёт, "
    "и о маленьких жестах, которые могут значить много! 🌍❤️",
    "Ваша занятость сегодня, без сомнения, была великолепна, но не забывайте о волшебстве маленьких вещей, "
    "как сданные отчёты. Ведь они тоже помогают делать мир лучше! 🌟",
    "Кажется, ваш день был наполнен чудесами, но волшебный мир отчётов тоже ждал вашего вклада. Подарите "
    "им "
    "частичку вашего внимания! ✨",
    "Ваши грандиозные планы на сегодня, видимо, забрали все время. Не пропустите шанс оставить свой след в "
    "благотворительном вкладе! 🚀",
    "Сегодняшний день, вероятно, был полон событий, но не забудьте о маленьком, но важном вкладе в наш "
    "общий "
    "мир. 😊",
    "Ваше мастерство сегодня зашкаливает, но не забывайте об отчёте и поделитесь этим волшебством в нашем "
    "общем сундучке "
    "добрых дел! 🌈",
    "Сегодня вы, должно быть, спасали мир! Не забудьте ещё и маленькое чудо сделать. 🌍",
    "Ваш день был наверняка полон героических свершений! Не упустите момент добавить к ним ещё одно — ваш "
    "вклад в нашу общую историю. 🦸‍♂",
    "Вы, как всегда, блестяще справляетесь с задачами! Но не забывайте рассказать о них в отчёте и "
    "оставить свой след в фонде добрых дел. "
    "💫",
    "Вы сегодня, как волшебник, творили чудеса! Не упустите шанс добавить волшебный штрих в коллекцию "
    "добрых "
    "дел. 🧙‍♂️",
    "Ваш день был, наверное, полон приключений! Не забудьте оставить след вашего приключения в казне "
    "великолепных свершений. 🚀",
    "Вы сегодня были, как супергерой, везде и всюду! Поделитесь частицей вашей суперсилы с командой добрых "
    "дел. 🦸‍♀️",
    "Сегодня вы, наверняка, творили историю! Поделитесь этой историей с фондом добрых дел. 📜",
    "Ваш день был, как эпос! Добавьте ещё одну главу, внесите свой вклад в книгу добрых дел. 📖",
    "Вы сегодня были звездой на небосводе! Не забудьте оставить искру в созвездии добрых дел. ⭐",
    "Ваша энергия сегодня, наверное, освещала города! Поделитесь этим светом, внесите свой вклад в наш "
    "фонд "
    "светлых начинаний. 💡",
    "Вы сегодня, кажется, вдохновляли мир! Не упустите шанс вдохновить и нас, добавьте свой вклад в фонд "
    "светлых свершений. 🌠",
    "Сегодня вы, наверное, покоряли вершины! Не забудьте поделиться этим успехом, добавьте свой вклад в "
    "фонд "
    "светлых свершений.. 🏔️",
    "Ваш день был, как карнавал! Поделитесь этим праздником, внесите свой вклад в фонд радостных "
    "моментов. 🎉",
    "Вы, наверняка, сегодня разгадывали тайны вселенной! Не упустите момент поделиться этими знаниями, "
    "добавив свой вклад в нашу вселенную добра. 🌌",
    "Ваш день был полон магии! Продолжайте творить чудеса, внося свой вклад в фонд волшебства. ✨",
    "Кажется, сегодня вы летали выше облаков! Не забудьте поделиться этим ощущением, внесите свой вклад в "
    "фонд светлых свершений. 🌤️",
    "Вы сегодня, вероятно, писали шедевры! Продолжайте творить искусство, добавив свой вклад в нашу "
    "галерею "
    "добрых дел. 🎨",
    "Ваш день был как великая одиссея! Не забудьте добавить главу об этом в нашу книгу великих и добрых "
    "дел. 📚",
    "Сегодня вы, наверное, укрощали бури! Поделитесь этой силой, внесите свой вклад в фонд "
    "благотворительности. 🌪️",
    "Вы сегодня, кажется, раскрашивали мир! Не упустите шанс раскрасить и картину добрых дел. 🖌️",
    "Сегодня вы, вероятно, творили чудеса! Не забудьте добавить свою волшебную пыльцу в фонд чудес. 🌟",
    "Ваш день был как грандиозное представление! Продолжайте удивлять, добавив свой вклад в фонд светлых "
    "свершений.. 🎭",
    "Кажется, сегодня вы собирали звёзды с небес! Поделитесь этим сиянием, добавьте искорку в фонд светлых "
    "свершений.. ✨",
    "Сегодня вы, наверняка, вели танец судьбы! Продолжайте вдохновлять, добавив свой шаг в наш танец "
    "добрых "
    "дел. 💃",
    "Ваш день был как невероятное путешествие! Оставьте свой след в путеводителе великих историй. 🗺️",
    "Сегодня вы, наверняка, плавали по волнам вдохновения! Продолжайте плыть, добавив свой вклад в фонд "
    "добрых дел. 🌊",
    "Ваш день был полон сверкающих моментов! Заставьте светить и наш мир, добавив свой вклад в наш фонд "
    "добра "
    "и благотворительности. 💎",
    "Сегодня вы, наверняка, творили музыку жизни! Продолжайте компонировать, добавив свою ноту в нашу "
    "симфонию добра. 🎶",
    "Вы сегодня, вероятно, путешествовали по облакам! Поделитесь этими высотами, добавив свой вклад в наш "
    "фонд настоящей доброты. ☁ "
]

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

morning_check_time = str(morning_time.hour + 10) + str(morning_time.minute + 10) + str(morning_time.second + 10)

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
    if message.from_user.last_name == None:
        return emoji.replace_emoji(message.from_user.first_name)

    full_name = ' '.join([emoji.replace_emoji(message.from_user.first_name), emoji.replace_emoji(message.from_user.last_name)])
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
    user_is_admin = is_admin(message)
    if user_is_admin:

        res = users_data.new_chat(message)
        if res:
            bot.send_message(message.chat.id, 'Привет, я бот помощник, теперь я буду помогать вам здесь \U0001F601')
        else:
            bot.send_message(message.chat.id, 'Я уже работаю в этом чате \U0001F601')
    else:
        bot.send_message(message.chat.id, 'Только администраторы чата могут использовать специальные команды')


@bot.message_handler(commands=['test'])
def create_table(message):
    print(emoji.replace_emoji(message.from_user.last_name))


@bot.message_handler(commands=['add'])
def my_helper(message):
    chat_id = "-1001992814051"
    message = bot.get_chat_member(chat_id, '803686181')
    message.from_user = message.user
    date = datetime.date(2024, 2, 8)
    users_data.new_user(message, chat_id=chat_id, full_date=date)


@bot.message_handler(commands=['report'])
def create_table(message):
    is_user_admin = is_admin(message)
    if is_user_admin:
        bot.send_message(message.from_user.id, 'Отчёт: для группы {chat}\n {report}'.format(
            chat=str(message.chat.title),
            report=users_data.data['chats'][str(message.chat.id)]['sheet_url']
        ))
    else:
        bot.send_message(message.chat.id, 'Только администраторы могут использовать специальные команды')



# @bot.message_handler(commands=['create_list'])
# def create_table(message):
#     print(users_data.data['sheet_id'])
#     res = Sheets.create_list('Test_Bot')
#     print(res)


# @bot.message_handler(commands=['create_user'])
# def add_user(message):
#     user_name = ' '.join([message.from_user.first_name, message.from_user.last_name])
#     res = Sheets.add_user(user_name)
#     print(res)


def send_user_update(message, report, value):
    full_name = get_full_name(message)
    date = datetime.datetime.now()
    date = '-'.join([str(date.year), str(date.month), str(date.day)])
    Sheets.change_sheet(users_data.data['chats'][str(message.chat.id)]['sheet_id'])
    Sheets.update_user(full_name, report, value, date)


def get_date_str():
    date = datetime.datetime.now()
    date = '-'.join([str(date.year), str(date.month), str(date.day)])
    return date


def check_user_table(message):
    full_name = get_full_name(message)
    Sheets.change_sheet(users_data.data['chats'][str(message.chat.id)]['sheet_id'])
    sheets_lists = Sheets.get_lists()
    if full_name in sheets_lists:
        print('Да')
        return True
    else:
        print('Нет')
        return False


print(report_type)


def logger(text):
    with open('log.txt', 'a', encoding='utf-8') as file:
        file.write(text + '\n')


def report_text(message):

    if str(message.chat.id) in users_data.data['chats'].keys():
        Sheets.change_sheet(users_data.data['chats'][str(message.chat.id)]['sheet_id'])


    user_is_admin = is_admin(message)

    # message.chat.title - Имя группы

    # TODO Включить проверку является ли пользователь админом группы
    if not user_is_admin:
        # Проверка существования чата в БД



        if report_type == 'Утренний':
            if message.text.lower().find('#оу') != -1:
                if str(message.chat.id) not in users_data.data['chats'].keys():
                    bot.send_message(message.chat.id,
                                     'Бот пока не работает в этой группе, для запуска бота напишите /start в чат')
                    return False
                if check_message_day(message.text, message.chat.id):
                    users_data.send_report(message)
        elif report_type == 'Вечерний':
            if message.text.lower().find('#ов') != -1:
                if str(message.chat.id) not in users_data.data['chats'].keys():
                    bot.send_message(message.chat.id,
                                     'Бот пока не работает в этой группе, для запуска бота напишите /start в чат')
                    return False
                if check_message_day(message.text, message.chat.id):
                    users_data.send_report(message)

        else:
            return False



@bot.edited_message_handler(content_types='text')
def message_edited(message):
    global lock
    lock.acquire()
    thread = Thread(target=report_text, args=(message,))
    thread.start()
    thread.join()
    lock.release()

@bot.message_handler(content_types='text')
def check_report(message):
    global lock
    lock.acquire()
    thread = Thread(target=report_text, args=(message,))
    thread.start()
    thread.join()
    lock.release()



def report_photo(message):
    if message.caption is None:
        return False



    if str(message.chat.id) in users_data.data['chats'].keys():
        Sheets.change_sheet(users_data.data['chats'][str(message.chat.id)]['sheet_id'])


    user_is_admin = is_admin(message)

    # message.chat.title - Имя группы

    # TODO Включить проверку является ли пользователь админом группы
    if not user_is_admin:

        if report_type == 'Утренний':
            if message.caption.lower().find('#оу') != -1:
                if str(message.chat.id) not in users_data.data['chats'].keys():
                    bot.send_message(message.chat.id,
                                     'Бот пока не работает в этой группе, для запуска бота напишите /start в чат')
                    return False
                if check_message_day(message.caption, message.chat.id):

                    users_data.send_report(message)

        elif report_type == 'Вечерний':
            if message.caption.lower().find('#ов') != -1:
                if str(message.chat.id) not in users_data.data['chats'].keys():
                    bot.send_message(message.chat.id,
                                     'Бот пока не работает в этой группе, для запуска бота напишите /start в чат')
                    return False
                if check_message_day(message.caption, message.chat.id):
                    users_data.send_report(message)

        else:
            return False



@bot.edited_message_handler(content_types=['photo'])
def photo_edited(message):
    global lock
    lock.acquire()
    thread = Thread(target=report_photo, args=(message,))
    thread.start()
    thread.join()
    lock.release()




@bot.message_handler(content_types=['photo'])
def photo_handler(message):
    global lock
    lock.acquire()
    thread = Thread(target=report_photo, args=(message,))
    thread.start()
    thread.join()
    lock.release()











# Проверочная функция для недельной проверки
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
                  misfire_grace_time=15 * 60,
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

lock = Lock()
scheduler.start()
try:
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
except Exception as e:
    print(e)
else:
    bot.infinity_polling(timeout=10, long_polling_timeout=5)


