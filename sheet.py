from oauth2client.service_account import ServiceAccountCredentials

from gspread_dataframe import set_with_dataframe
from pandas import DataFrame
import gspread
from datetime import date

from month import Month

class Sheet:

    # If modifying these scopes, delete the file token.json.
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    CREDENTIALS_PATH = 'credentials/sa_program_update.json'

    def __init__(self, program_name:str, sheet_id:str, duplicate:bool):
        # Verify user or use existing credentials
        creds = self.verify_user()
        # Authorise Google Cloud access
        self.gc = gspread.authorize(creds)

        # If run as a duplicate run updates on a copy of the sheet for testing
        if duplicate:
            print(f"\n\tDuplicating program: {program_name.capitalize()}")
            sheet_id_f = self.duplicate_sheet(program_name, sheet_id)
            print(f"\n\tNew sheet Link: https://docs.google.com/spreadsheets/d/{sheet_id_f}")
        else:
            sheet_id_f = sheet_id

        # Open training program
        self.g_sheet = self.gc.open_by_key(
            sheet_id_f
        )

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
            month_data = \
                self.g_sheet.worksheet(month_sheet_name).get_all_values()

            month_instance = Month(
                data=month_data,
                g_sheet=self.g_sheet,
                sheet_name=month_sheet_name,
                verbose=verbose
            )
            month_sessions[month_sheet_name] = month_instance
            
        return(month_sessions)
    
    def duplicate_sheet(self, program_name:str, sheet_id:str):
        new_spreadsheet = self.gc.copy(
            sheet_id, 
            title=f"[Test] - Root Program:: {program_name.capitalize()} {date.today()}", 
            copy_permissions=True,
            folder_id="1rdON9vpywCPYp_a_gwxzOciYVQm1DdyR"
        )

        return(new_spreadsheet.id)