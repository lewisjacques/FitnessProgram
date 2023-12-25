from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from gspread_dataframe import set_with_dataframe
from pandas import DataFrame
import gspread
import os

from month import Month

class Sheet:

    # If modifying these scopes, delete the file token.json.
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets'
    ]

    def __init__(self, sheet_id):
        # Verify user or use existing credentials
        creds = self.verify_user()
        # Authorise Google Cloud access
        gc = gspread.authorize(creds)
        # Open training program
        self.g_sheet = gc.open_by_key(sheet_id)

    def verify_user(self):
        """
        Verify permissions to the Google Sheet using a tokenised method.
        On my to-do  list to change this to a service account with universal
        credentials to make access more straight-forward
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

        return(creds)
    
    def write_to_sheet(self, df:DataFrame, tab_name:str):
        """
        Write data frame to a worksheet

        Args:
            df (DataFrame): DataFrame provided
            tab_name (str): Worksheet to  push the data  to
        """
        # Select comment sheet
        worksheet = self.g_sheet.worksheet(tab_name)
        worksheet.clear()

        set_with_dataframe(
            worksheet=worksheet, 
            dataframe=df, 
            include_index=False,
            include_column_header=True, 
            resize=True
        )

    def parse_months(self, explicit_format_months:list):
        """
        Parse months that are using the new format where exercise notes
        are stated explicitly next to the exercise rather than in the comment
        of the cell with the exercise

        Args:
            explicit_format_months (list): List of months using the new methodology
            where each element of the list represents a sheet tab
        """

        month_sessions = {}
        for month_sheet_name in explicit_format_months:
            month_data = self.g_sheet.worksheet(month_sheet_name)
            month_instance = Month(month_data.get_all_values())
            month_sessions[month_sheet_name] = month_instance
            
        return(month_sessions)