import json

default = {'chats': {100: {'users': {1: {'user_name': 'Stas', 'is_done': True}}}}}


def get_db():
    with open('db.json', 'r') as file:
        res = json.load(file)
    return res


def set_db(data):
    with open('db.json', 'w') as file:
        json.dump(data, file, indent=2)


def get_white_list():
    with open('white_list.json', 'r') as file:
        res = json.load(file)
    return res


def add_to_white_list(user_id):
    res = get_white_list()
    res['users'].append(str(user_id))
    with open('white_list.json', 'w') as file:
        json.dump(res, file, indent=2)
