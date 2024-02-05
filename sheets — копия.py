# -*- coding: cp1251 -*-

# ���������� ����������
import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = 'token.json'  # ��� ����� � �������� ������, �� ������ ���������� ����

# ������ ����� �� �����
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])

httpAuth = credentials.authorize(httplib2.Http()) # ������������ � �������
service = apiclient.discovery.build('sheets', 'v4', http = httpAuth) # �������� ������ � ��������� � 4 ������ API

# spreadsheet = service.spreadsheets().create(body = {
#     'properties': {'title': '������ �������� ��������', 'locale': 'ru_RU'},
#     'sheets': [{'properties': {'sheetType': 'GRID',
#                                'sheetId': 0,
#                                'title': '���� ����� ����',
#                                'gridProperties': {'rowCount': 100, 'columnCount': 15}}}]
# }).execute()��������� ������������� �����

class engine:

    SHEET_ID = "1oNrPwxW1SzxL5O42lLafmPlQTvH3XBzPsjgz9NJk1ys"

    @classmethod
    def change_sheet(cls, id):
        cls.SHEET_ID = id

    @classmethod
    def connect(cls):
        driveService = apiclient.discovery.build('drive', 'v3',
                                                 http=httpAuth)  # �������� ������ � Google Drive � 3 ������ API
        access = driveService.permissions().create(
            fileId=SHEET_ID,
            body={'type': 'user', 'role': 'writer', 'emailAddress': 'stasarh2002@gmail.com'},
            # ��������� ������ �� ��������������
            fields='id'
        ).execute()


engine.change_sheet('asdfagw')
print(engine.SHEET_ID)


print('https://docs.google.com/spreadsheets/d/' + SHEET_ID)
driveService = apiclient.discovery.build('drive', 'v3', http = httpAuth) # �������� ������ � Google Drive � 3 ������ API
access = driveService.permissions().create(
    fileId = SHEET_ID,
    body = {'type': 'user', 'role': 'writer', 'emailAddress': 'stasarh2002@gmail.com'},  # ��������� ������ �� ��������������
    fields = 'id'
).execute()






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

spreadsheet = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
sheetList = spreadsheet.get('sheets')
for sheet in sheetList:
    print(sheet['properties']['sheetId'], sheet['properties']['title'])

sheetId = sheetList[0]['properties']['sheetId']

print('�� ����� ������������ ���� � Id = ', sheetId)

results = service.spreadsheets().values().batchUpdate(spreadsheetId = SHEET_ID, body = {
    "valueInputOption": "USER_ENTERED", # ������ ��������������, ��� �������� ������������� (��������� �������� ������)
    "data": [
        {"range": "���� ����� ����!B2:D5",
         "majorDimension": "ROWS",     # ������� ��������� ������, ����� �������
         "values": [
                    ["������ B1", "������ C1", "������ D1"], # ��������� ������ ������
                    ['25', "=6*6", "55"],
                    ["������ B1", "������ C1", "������ D1"]
                   ]}
    ]
}).execute()

