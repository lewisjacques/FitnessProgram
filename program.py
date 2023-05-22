from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from comment_parser import RawCommentFile, APIComment

import os

class Program:
    
    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    PROGRAM_SHEET_ID = "1LyZsxwUsc5PSdzQT_2G3HZxty9rWwR-laV48spNrOQI"

    def __init__(self, comment_file_path:str, api_extract:bool):
        """
        Extract comments from requested locations and input them onto
        a dedicated sheet to keep track of the logging

        Args:
            comment_file_path (str): file-path to static comments
            api_extract (bool): trigger to extract meta-data from GSheets
        """
        self.service = self.verify_user()

        ### --- Get Archived Comments --- ###

        with open(comment_file_path) as coms:
            archive_comments = ''.join(coms.readlines())

        self.raw_comments = RawCommentFile(archive_comments)

        ### --- Get Sheets comments through the API --- ###

        if api_extract:
            # self.get_program(
            #     sheet_id=self.PROGRAM_SHEET_ID,
            #     range="Exercises!A1:E"
            # )
            
            # values = result.get('values', [])
            # c_parser_api = APIComment(values)
            print("Google Sheets API doesn\'t allow this functionality yet")

        ### --- Write Comments to Sheet --- ###

        for com in self.raw_comments.parsed_comments:
            print(com.print_comment())
        
    def verify_user(self):
        """
        Verify permissions to the Google Sheet
        """
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
    
    def get_program(self, sheet_id:str, range:str):
        """
        Function to return all cell data in a given range

        Args:
            sheet_id (str): Google sheets ID
            range (str): Worksheet range
        """
        sheet = self.service.spreadsheets()
        self.result = sheet.values()
        self.get_result_vals = self.result.get(
            spreadsheetId=sheet_id,
            range=range
        )

        