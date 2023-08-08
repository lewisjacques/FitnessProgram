from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from gspread_dataframe import set_with_dataframe

from comment import RawCommentFile, APIComment

import pandas as pd
import gspread
import os

class Program:
    
    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    PROGRAM_SHEET_ID = "1LyZsxwUsc5PSdzQT_2G3HZxty9rWwR-laV48spNrOQI"

    def __init__(
            self, 
            comment_file_path:str=None, 
            api_extract:bool=False,
            write_to_sheet:bool=True,
            write_to_file:str|bool=False
        ):
        """
        Extract comments from requested locations and input them onto
        a dedicated sheet to keep track of the logging

        Args:
            comment_file_path (str): file-path to static comments
            api_extract (bool): trigger to extract meta-data from GSheets
        """
        self.service = self.verify_user()

        ### --- Get Sheets comments through the API --- ###
        if api_extract:
            self.raw_comments = self.get_api_comments()
            print("Google Sheets API doesn\'t allow this functionality yet")

        ### --- Get Archived Comments --- ###
        else:
            if comment_file_path is None:
                self.comment_df = pd.read_csv("data/parsed_comments.csv")
            else:
                print("Opening raw comments")
                with open(comment_file_path) as coms:
                    archive_comments = ''.join(coms.readlines())
                # Parse the raw comments
                print("Parsing raw comments")
                self.raw_comments = RawCommentFile(archive_comments)

                ### --- Build Data-Frame --- ###
                print("Building comment data-frame")
                self.comment_df = self.build_comment_df()
                print(self.comment_df.head())
                print(self.comment_df.tail())

        ## -- Write to Local File -- ##
        if write_to_file:
            print("Writing to file")
            self.comment_df.to_csv("data/parsed_comments.csv", index=False)

        ### --- Write Data-Frame to Sheet --- ###
        if write_to_sheet :
            print("Writing to sheet")
            self.write_to_sheet(
                df=self.comment_df,
                sheet_id="1LyZsxwUsc5PSdzQT_2G3HZxty9rWwR-laV48spNrOQI",
                tab_name="Comments (via Python)"
            )
        
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
        self.creds = creds
        return(service)
    
    def build_comment_df(self):
        # Convert parsed comments into a dataframe
        comment_df = pd.DataFrame(
            columns=[
                "Sheet",
                "Cell",
                "Cell Data",
                "Time-Stamp",
                "Comment"
            ]
        )
        for com in self.raw_comments.parsed_comments:
            comment_df = pd.concat(
                [
                    pd.DataFrame({
                        "Sheet": com.sheet,
                        "Cell": com.cell,
                        "Cell Data": com.exercise,
                        "Time-Stamp": com.datetime,
                        "Comment": com.comment
                    }, index=[0]),
                    comment_df
                ],
                ignore_index=True
            )
        return(comment_df)
    
    def write_to_sheet(
        self, 
        df:pd.DataFrame, 
        sheet_id:str, 
        tab_name:str
        ):

        gc = gspread.authorize(self.creds)

        # Open training program
        gs = gc.open_by_key(sheet_id)
        # Select comment sheet
        worksheet = gs.worksheet(tab_name)
        worksheet.clear()

        set_with_dataframe(
            worksheet=worksheet, 
            dataframe=df, 
            include_index=False,
            include_column_header=True, 
            resize=True
        )
    
    def get_api_comments(self):
        """
        Function to return all comments from all sheets through the API

        Args:
        """
        return

    def get_ex_comments(self, exercise:str):
        parsed_comments_filtered = \
            self.comment_df.loc[
                self.comment_df['Cell Data']==exercise,
                ['Comment']
            ].tail(1)
        return(parsed_comments_filtered)