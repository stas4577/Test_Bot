# -*- coding: cp1251 -*-

# Подключаем библиотеки
import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = 'token.json'  # Имя файла с закрытым ключом, вы должны подставить свое

# Читаем ключи из файла
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])

httpAuth = credentials.authorize(httplib2.Http()) # Авторизуемся в системе
service = apiclient.discovery.build('sheets', 'v4', http = httpAuth) # Выбираем работу с таблицами и 4 версию API

# spreadsheet = service.spreadsheets().create(body = {
#     'properties': {'title': 'Первый тестовый документ', 'locale': 'ru_RU'},
#     'sheets': [{'properties': {'sheetType': 'GRID',
#                                'sheetId': 0,
#                                'title': 'Лист номер один',
#                                'gridProperties': {'rowCount': 100, 'columnCount': 15}}}]
# }).execute()сохраняем идентификатор файла

class engine:

    SHEET_ID = "1oNrPwxW1SzxL5O42lLafmPlQTvH3XBzPsjgz9NJk1ys"

    @classmethod
    def change_sheet(cls, id):
        cls.SHEET_ID = id

    @classmethod
    def connect(cls):
        driveService = apiclient.discovery.build('drive', 'v3',
                                                 http=httpAuth)  # Выбираем работу с Google Drive и 3 версию API
        access = driveService.permissions().create(
            fileId=SHEET_ID,
            body={'type': 'user', 'role': 'writer', 'emailAddress': 'stasarh2002@gmail.com'},
            # Открываем доступ на редактирование
            fields='id'
        ).execute()


engine.change_sheet('asdfagw')
print(engine.SHEET_ID)


print('https://docs.google.com/spreadsheets/d/' + SHEET_ID)
driveService = apiclient.discovery.build('drive', 'v3', http = httpAuth) # Выбираем работу с Google Drive и 3 версию API
access = driveService.permissions().create(
    fileId = SHEET_ID,
    body = {'type': 'user', 'role': 'writer', 'emailAddress': 'stasarh2002@gmail.com'},  # Открываем доступ на редактирование
    fields = 'id'
).execute()






# Добавление листа
# results = service.spreadsheets().batchUpdate(
#     spreadsheetId = spreadsheetId,
#     body =
# {
#   "requests": [
#     {
#       "addSheet": {
#         "properties": {
#           "title": "Новый лист",
#           "gridProperties": {
#             "rowCount": 20,
#             "columnCount": 12
#           }
#         }
#       }
#     }
#   ]
# }).execute()

spreadsheet = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
sheetList = spreadsheet.get('sheets')
for sheet in sheetList:
    print(sheet['properties']['sheetId'], sheet['properties']['title'])

sheetId = sheetList[0]['properties']['sheetId']

print('Мы будем использовать лист с Id = ', sheetId)

results = service.spreadsheets().values().batchUpdate(spreadsheetId = SHEET_ID, body = {
    "valueInputOption": "USER_ENTERED", # Данные воспринимаются, как вводимые пользователем (считается значение формул)
    "data": [
        {"range": "Лист номер один!B2:D5",
         "majorDimension": "ROWS",     # Сначала заполнять строки, затем столбцы
         "values": [
                    ["Ячейка B1", "Ячейка C1", "Ячейка D1"], # Заполняем первую строку
                    ['25', "=6*6", "55"],
                    ["Ячейка B1", "Ячейка C1", "Ячейка D1"]
                   ]}
    ]
}).execute()

