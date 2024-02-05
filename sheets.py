# -*- coding: cp1251 -*-

# Подключаем библиотеки
import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

# spreadsheet = service.spreadsheets().create(body = {
#     'properties': {'title': 'Первый тестовый документ', 'locale': 'ru_RU'},
#     'sheets': [{'properties': {'sheetType': 'GRID',
#                                'sheetId': 0,
#                                'title': 'Лист номер один',
#                                'gridProperties': {'rowCount': 100, 'columnCount': 15}}}]
# }).execute()сохраняем идентификатор файла


TIME_TAGS = {
    'Утренний': 'B',
    'Вечерний': 'C',
    'Недельний': 'D',
    'Штраф': 'E',
    'Дата штрафа': 'F',
    'За отчёт': 'G'
}


class Sheets:
    httpAuth = None
    driveService = None
    service = None
    sheet_id = "1Pa-9_336uLKvtbDhJbt9MF5Ag1lTDMCC4VtJF1BV1fs"
    mail = 'stasarh2002@gmail.com'
    api_url = 'https://docs.google.com/spreadsheets/d/'

    @classmethod
    def change_sheet(cls, id):
        cls.SHEET_ID = id

    @classmethod
    def colnum_string(cls, n):
        string = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            string = chr(65 + remainder) + string
        return string

    @classmethod
    def connect(cls):
        CREDENTIALS_FILE = 'token.json'  # Имя файла с закрытым ключом, вы должны подставить свое

        # Читаем ключи из файла
        credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE,
                                                                       ['https://www.googleapis.com/auth/spreadsheets',
                                                                        'https://www.googleapis.com/auth/drive'])

        cls.httpAuth = credentials.authorize(httplib2.Http())  # Авторизуемся в системе
        cls.service = apiclient.discovery.build('sheets', 'v4',
                                                http=cls.httpAuth)  # Выбираем работу с таблицами и 4 версию API

        cls.driveService = apiclient.discovery.build('drive', 'v3',
                                                     http=cls.httpAuth)  # Выбираем работу с Google Drive и 3 версию API

    @classmethod
    def create_table(cls, name: str, chat_name: str):
        spreadsheet = cls.service.spreadsheets().create(body={
            'properties': {'title': name, 'locale': 'ru_RU'},
            'sheets': [{'properties': {'sheetType': 'GRID',
                                       'sheetId': 0,
                                       'title': chat_name,
                                       'gridProperties': {'rowCount': 100, 'columnCount': 15}}}]
        }).execute()
        cls.access = cls.driveService.permissions().create(
            fileId=spreadsheet['spreadsheetId'],
            body={'type': 'user', 'role': 'writer', 'emailAddress': 'stasarh2002@gmail.com'},
            # Открываем доступ на редактирование
            fields='id'
        ).execute()

        res = cls.api_url + spreadsheet['spreadsheetId']
        return res

    @classmethod
    def create_list(cls, name: str):
        results = cls.service.spreadsheets().batchUpdate(
            spreadsheetId=cls.sheet_id,
            body=
            {
                "requests": [
                    {
                        "addSheet": {
                            "properties": {
                                "title": name,
                                "gridProperties": {
                                    "rowCount": 80,
                                    "columnCount": 40
                                }
                            }
                        }
                    }
                ]
            }).execute()
        print(results)
        return results

    @classmethod
    def set_alligment(cls, list_id: str):
        results = cls.service.spreadsheets().batchUpdate(
            spreadsheetId=cls.sheet_id,
            body=
            {
                "requests":
                    [
                        {
                            "repeatCell":
                                {
                                    "cell":
                                        {
                                            "userEnteredFormat":
                                                {
                                                    "horizontalAlignment": 'CENTER',
                                                }
                                        },
                                    "range":
                                        {
                                            "sheetId": list_id,
                                            "startRowIndex": 0,
                                            "endRowIndex": 100,
                                            "startColumnIndex": 0,
                                            "endColumnIndex": 100
                                        },
                                    "fields": "userEnteredFormat"
                                }
                        }
                    ]
            }).execute()

    @classmethod
    def update_user(cls, list_name: str, tag: str, value: str, date: str):
        ranges = ["{list_name}!A2:A100".format(list_name=list_name)]  #

        results = cls.service.spreadsheets().values().batchGet(spreadsheetId=cls.sheet_id,
                                                               ranges=ranges,
                                                               valueRenderOption='FORMATTED_VALUE',
                                                               dateTimeRenderOption='FORMATTED_STRING').execute()
        sheet_values = results['valueRanges'][0]['values']
        print(sheet_values)
        print(date)
        row_num = 0
        for i_date in range(len(sheet_values)):
            if sheet_values[i_date][0] == date:
                row_num = i_date + 2
                break
        results = cls.service.spreadsheets().values().batchUpdate(spreadsheetId=cls.sheet_id, body={
            "valueInputOption": "USER_ENTERED",
            # Данные воспринимаются, как вводимые пользователем (считается значение формул)
            "data": [
                {
                    "range": "{list_name}!{letter}{num}:{letter}{num}".format(
                        list_name=list_name,
                        letter=TIME_TAGS[tag],
                        num=row_num
                    ),
                    "majorDimension": "ROWS",  # Сначала заполнять строки, затем столбцы
                    "values": [
                        [value],
                    ]
                }
            ],

        }).execute()

    @classmethod
    def add_user(cls, user_name: str):
        result = cls.service.spreadsheets().batchUpdate(
            spreadsheetId=cls.sheet_id,
            body=
            {
                "requests": [
                    {

                        "addSheet": {
                            "properties": {
                                "title": user_name,
                                "gridProperties": {
                                    "rowCount": 80,
                                    "columnCount": 40
                                },
                            }
                        },
                    }
                ]
            }).execute()
        print(result)
        res_list_id = result['replies'][0]['addSheet']['properties']['sheetId']

        results = cls.service.spreadsheets().batchUpdate(
            spreadsheetId=cls.sheet_id,
            body=
            {
                "requests":
                    [
                        {
                            "updateDimensionProperties": {
                                "range": {
                                    "sheetId": res_list_id,
                                    "dimension": "COLUMNS",
                                    "startIndex": 0,
                                    "endIndex": 7
                                },
                                "properties": {
                                    "pixelSize": 200
                                },
                                "fields": "pixelSize"
                            }
                        },
                        {
                            "repeatCell":
                                {
                                    "cell":
                                        {
                                            "userEnteredFormat":
                                                {
                                                    "horizontalAlignment": 'CENTER',
                                                    "backgroundColor": {
                                                        "red": 0.8,
                                                        "green": 0.8,
                                                        "blue": 0.8,
                                                        "alpha": 1
                                                    },
                                                    "textFormat":
                                                        {
                                                            "bold": True,
                                                            "fontSize": 12
                                                        }
                                                }
                                        },
                                    "range":
                                        {
                                            "sheetId": res_list_id,
                                            "startRowIndex": 0,
                                            "endRowIndex": 1,
                                            "startColumnIndex": 0,
                                            "endColumnIndex": 7
                                        },
                                    "fields": "userEnteredFormat"
                                }
                        }
                    ]
            }).execute()

        res = cls.service.spreadsheets().values().batchUpdate(spreadsheetId=cls.sheet_id, body={
            "valueInputOption": "USER_ENTERED",
            # Данные воспринимаются, как вводимые пользователем (считается значение формул)
            "data": [
                {"range": "{list_name}!A1:G1".format(list_name=user_name),
                 "majorDimension": "ROWS",  # Сначала заполнять строки, затем столбцы
                 "values": [
                     [
                         "Дата",
                         "Утренний отчёт",
                         "Вечерний отчёт",
                         "Недельный отчёт",
                         "Штраф",
                         "Дата уплаты штрафа",
                         "За отчёт"
                     ],
                 ]}
            ]
        }).execute()

        cls.set_alligment(res_list_id)

        return result

    @classmethod
    def new_day(cls, date, list_name: str):
        resource = {
            "majorDimension": "ROWS",
            "values": [[date]]
        }
        range = "{list_name}!A:A".format(list_name=list_name)
        cls.service.spreadsheets().values().append(
            spreadsheetId=cls.sheet_id,
            range=range,
            body=resource,
            valueInputOption="USER_ENTERED"
        ).execute()

    @classmethod
    def test(cls, user_name: str):
        result = cls.service.spreadsheets().values().append(
            spreadsheetId=cls.sheet_id,
            range="Test_Bot!C1:C100",
            valueInputOption="USER_ENTERED",
            body={
                "majorDimension": "ROWS",
                "values": [[user_name]]
            },
        ).execute()

        range_name = "Test_Bot!1:1"
        response = cls.service.spreadsheets().values().get(
            spreadsheetId=cls.sheet_id,
            range=range_name
        ).execute()
        print(response['values'][0])
        print(len(response['values'][0]))
        print(cls.colnum_string(len(response['values'][0])))

# print(Engine.sheet_id)
# Engine.connect()
#
# print('https://docs.google.com/spreadsheets/d/' + SHEET_ID)


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

# spreadsheet = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
# sheetList = spreadsheet.get('sheets')
# for sheet in sheetList:
#     print(sheet['properties']['sheetId'], sheet['properties']['title'])
#
# sheetId = sheetList[0]['properties']['sheetId']
#
# print('Мы будем использовать лист с Id = ', sheetId)
#
# results = service.spreadsheets().values().batchUpdate(spreadsheetId=SHEET_ID, body={
#     "valueInputOption": "USER_ENTERED",  # Данные воспринимаются, как вводимые пользователем (считается значение формул)
#     "data": [
#         {"range": "Лист номер один!B2:D5",
#          "majorDimension": "ROWS",  # Сначала заполнять строки, затем столбцы
#          "values": [
#              ["Ячейка B1", "Ячейка C1", "Ячейка D1"],  # Заполняем первую строку
#              ['25', "=6*6", "55"],
#              ["Ячейка B1", "Ячейка C1", "Ячейка D1"]
#          ]}
#     ]
# }).execute()
