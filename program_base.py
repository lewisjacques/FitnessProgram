from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from api_requests import GoogleSheetsAPIRequests
from datetime import date
import gspread

class ProgramBase:
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    CREDENTIALS_PATH = 'credentials/sa_program_update.json'

    def __init__(self, spreadsheet_id):
        # Verify user or use existing credentials
        creds = self.verify_user()
        # Service object to apply conditional formatting
        self.service = build('sheets', 'v4', credentials=creds)

        # Authorise Google Cloud access
        self.gc = gspread.authorize(creds)

        # Open training program
        self.g_sheet = self.gc.open_by_key(spreadsheet_id)
        # Also initialise Google Sheets Request instance for handling API reqs
        self.gsar = GoogleSheetsAPIRequests(self.g_sheet)

        self.spreadsheet_id = spreadsheet_id

    def duplicate_sheet(self, program_name:str, spreadsheet_id:str):
        new_spreadsheet = self.gc.copy(
            spreadsheet_id, 
            title=f"[Test] - Root Program:: {program_name.capitalize()} {date.today()}", 
            copy_permissions=True,
            folder_id="1rdON9vpywCPYp_a_gwxzOciYVQm1DdyR"
        )
        return(new_spreadsheet.id)
    
    def find_sheet_id(self, sheet_name:str):
        sheet_id = self.g_sheet.worksheet(
            sheet_name
        )._properties['sheetId']
        return(sheet_id)

    def verify_user(self):
        """
        Return the credentials object derived from the service account
        credentials file

        Returns:
            ServiceAccountCredentials: Google Sheets API credentials
        """

        creds = ServiceAccountCredentials.from_json_keyfile_name(
            self.CREDENTIALS_PATH,
            self.SCOPES
        )
        return creds