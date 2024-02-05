import json

default = {'chats': {100: {'users': {1: {'user_name': 'Stas', 'is_done': True}}}, 'day': '1'}}


def get_db():
    with open('db.json', 'r') as file:
        res = json.load(file)
    return res


def set_db(data):
    with open('db.json', 'w') as file:
        json.dump(data, file, indent=2)


