# -*- coding: cp1251 -*-

# ���������� ����������
import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import time

# spreadsheet = service.spreadsheets().create(body = {
#     'properties': {'title': '������ �������� ��������', 'locale': 'ru_RU'},
#     'sheets': [{'properties': {'sheetType': 'GRID',
#                                'sheetId': 0,
#                                'title': '���� ����� ����',
#                                'gridProperties': {'rowCount': 100, 'columnCount': 15}}}]
# }).execute()��������� ������������� �����


TIME_TAGS = {
    '��������': 'B',
    '��������': 'C',
    '���������': 'D',
    '�����': 'E',
    '���� ������': 'F',
    '�� �����': 'G'
}


class Sheets:
    httpAuth = None
    driveService = None
    service = None
    sheet_id = "1Pa-9_336uLKvtbDhJbt9MF5Ag1lTDMCC4VtJF1BV1fs"
    mail = 'stasarh2002@gmail.com'
    api_url = 'https://docs.google.com/spreadsheets/d/'

    @classmethod
    def change_sheet(cls, change_id):
        cls.sheet_id = change_id

    @classmethod
    def colnum_string(cls, n):
        string = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            string = chr(65 + remainder) + string
        return string

    @classmethod
    def connect(cls):
        CREDENTIALS_FILE = 'token.json'  # ��� ����� � �������� ������, �� ������ ���������� ����

        # ������ ����� �� �����
        credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE,
                                                                       ['https://www.googleapis.com/auth/spreadsheets',
                                                                        'https://www.googleapis.com/auth/spreadsheets.readonly',
                                                                        'https://www.googleapis.com/auth/drive'])

        cls.httpAuth = credentials.authorize(httplib2.Http())  # ������������ � �������
        cls.service = apiclient.discovery.build('sheets', 'v4',
                                                http=cls.httpAuth)  # �������� ������ � ��������� � 4 ������ API

        cls.driveService = apiclient.discovery.build('drive', 'v3',
                                                     http=cls.httpAuth)  # �������� ������ � Google Drive � 3 ������ API


    @classmethod
    def get_lists(cls):
        res = cls.service.spreadsheets().get(spreadsheetId=cls.sheet_id).execute()
        sheetList = res.get('sheets')
        res = []
        for item in sheetList:
            print(item)
            res.append(item['properties']['title'])
        return res

    @classmethod
    def create_table(cls, table_name: str):
        spreadsheet = cls.service.spreadsheets().create(body={
            'properties': {'title': table_name, 'locale': 'ru_RU'},

        }).execute()
        cls.access = cls.driveService.permissions().create(
            fileId=spreadsheet['spreadsheetId'],
            body={'type': 'anyone', 'role': 'reader'},
            # ��������� ������ �� ��������������
            fields='id'
        ).execute()

        res = cls.api_url + spreadsheet['spreadsheetId']
        return res, spreadsheet['spreadsheetId']

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
        row_num = 0
        for i_date in range(len(sheet_values)):
            if sheet_values[i_date][0] == date:
                row_num = i_date + 2
                break
        if row_num == 0:
            row_num = 2
        results = cls.service.spreadsheets().values().batchUpdate(spreadsheetId=cls.sheet_id, body={
            "valueInputOption": "USER_ENTERED",
            # ������ ��������������, ��� �������� ������������� (��������� �������� ������)
            "data": [
                {
                    "range": "{list_name}!{letter}{num}:{letter}{num}".format(
                        list_name=list_name,
                        letter=TIME_TAGS[tag],
                        num=row_num
                    ),
                    "majorDimension": "ROWS",  # ������� ��������� ������, ����� �������
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
                    },

                ]
            }).execute()
        print('������� ���� ��� ������������:', user_name)
        res_list_id = result['replies'][0]['addSheet']['properties']['sheetId']
        cls.set_header_width(res_list_id)
        date = datetime.datetime.now()
        date = '-'.join([str(date.year), str(date.month), str(date.day)])


        res = cls.service.spreadsheets().values().batchUpdate(spreadsheetId=cls.sheet_id, body={
            "valueInputOption": "USER_ENTERED",
            # ������ ��������������, ��� �������� ������������� (��������� �������� ������)
            "data": [
                {"range": "{list_name}!A1:G1".format(list_name=user_name),
                 "majorDimension": "ROWS",  # ������� ��������� ������, ����� �������
                 "values": [
                     [
                         "����",
                         "�������� �����",
                         "�������� �����",
                         "��������� �����",
                         "�����",
                         "���� ������ ������",
                         "�� �����"
                     ],
                 ]}
            ]
        }).execute()

        cls.set_alligment(res_list_id)
        cls.new_day(date, user_name)
        print('������� ���� ��� ������ ������������')

        return result

    @classmethod
    def new_day(cls, date, list_name: str):

        resource = {
            "majorDimension": "ROWS",
            "values": [[date]]
        }
        range = "{list_name}!A:A".format(list_name=list_name)
        res = cls.service.spreadsheets().values().append(
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

    @classmethod
    def set_header_width(cls, sheet_id):
        results = cls.service.spreadsheets().batchUpdate(spreadsheetId=cls.sheet_id, body={
            "requests": [

                # ������ ������ ������� A: 20 ��������
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",  # ������ ������ �������
                            "startIndex": 0,  # ��������� ���������� � ����
                            "endIndex": 7  # �� ������� ����� startIndex �� endIndex - 1 (endIndex �� ������!)
                        },
                        "properties": {
                            "pixelSize": 200  # ������ � ��������
                        },
                        "fields": "pixelSize"  # ���������, ��� ����� ������������ �������� pixelSize
                    }
                },
            ]
        }).execute()

# print(Engine.sheet_id)
# Engine.connect()
#
# print('https://docs.google.com/spreadsheets/d/' + SHEET_ID)


# ���������� �����
# results = service.spreadsheets().batchUpdate(
#     spreadsheetId = spreadsheetId,
#     body =
# {
#   "requests": [
#     {
#       "addSheet": {
#         "properties": {
#           "title": "����� ����",
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
# print('�� ����� ������������ ���� � Id = ', sheetId)
#
# results = service.spreadsheets().values().batchUpdate(spreadsheetId=SHEET_ID, body={
#     "valueInputOption": "USER_ENTERED",  # ������ ��������������, ��� �������� ������������� (��������� �������� ������)
#     "data": [
#         {"range": "���� ����� ����!B2:D5",
#          "majorDimension": "ROWS",  # ������� ��������� ������, ����� �������
#          "values": [
#              ["������ B1", "������ C1", "������ D1"],  # ��������� ������ ������
#              ['25', "=6*6", "55"],
#              ["������ B1", "������ C1", "������ D1"]
#          ]}
#     ]
# }).execute()
