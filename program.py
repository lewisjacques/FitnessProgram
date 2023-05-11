from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import os

class Program:
    
    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    PROGRAM_SHEET_ID = "1LyZsxwUsc5PSdzQT_2G3HZxty9rWwR-laV48spNrOQI"

    def __init__(self):
        self.service = self.verify_user()
        self.get_program(sheet_id=self.PROGRAM_SHEET_ID)

    def verify_user(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes first
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        service = build('sheets', 'v4', credentials=creds)
        return(service)
    
    def get_program(self, sheet_id):
        sheet = self.service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=sheet_id,
            range="Exercises!A1:E"
        ).execute()
        values = result.get('values', [])
        print(values)
