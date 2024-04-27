from oauth2client.service_account import ServiceAccountCredentials

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
    CREDENTIALS_PATH = 'credentials/sa_program_update.json'

    def __init__(self, sheet_id):
        # Verify user or use existing credentials
        creds = self.verify_user()
        # Authorise Google Cloud access
        gc = gspread.authorize(creds)
        # Open training program
        self.g_sheet = gc.open_by_key(sheet_id)

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

    def parse_months(self, explicit_format_months:list, verbose:bool):
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
            print(f"\tParsing Sheet: {month_sheet_name}")
            month_data = self.g_sheet.worksheet(month_sheet_name)
            month_instance = Month(
                data=month_data.get_all_values(),
                verbose=verbose
            )
            # month_instance.clean_month(
            #     self.g_sheet,
            #     month_sheet_name
            # )
            month_sessions[month_sheet_name] = month_instance
            
        return(month_sessions)