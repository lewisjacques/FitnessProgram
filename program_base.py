from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from datetime import date
import gspread

class ProgramBase:
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    CREDENTIALS_PATH = 'credentials/sa_program_update.json'

    # Shared state
    _spreadsheet_id = None
    _g_sheet = None
    _initialized = False
    _service = None

    def __init__(self, spreadsheet_id):
        # Only initialize shared state once
        
        if not ProgramBase._initialized:
            print(f"Current spreadsheet id: {self.spreadsheet_id}")
            print("Initializing ProgramBase...")
            creds = self.verify_user()
            ProgramBase._initialized = True
            print("Initialising variables")
            self.init_variables(spreadsheet_id, creds)
            # Service object to apply conditional formatting
            ProgramBase._service = build('sheets', 'v4', credentials=creds)
        else:
            print(f"Current spreadsheet id: {self.spreadsheet_id}")
            print(f"New spreadsheet id: {spreadsheet_id}")

    # Modify class level specific variables, not instance level
    @classmethod
    def init_variables(cls, spreadsheet_id: str, creds):
        """
        Initialize the shared class-level variables
        """
        cls._spreadsheet_id = spreadsheet_id
        # Authorize Google Cloud access
        gc = gspread.authorize(creds)
        # Open training program
        cls._g_sheet = gc.open_by_key(spreadsheet_id)

    @property
    def spreadsheet_id(self):
        return ProgramBase._spreadsheet_id

    @property
    def g_sheet(self):
        return ProgramBase._g_sheet
    
    @property
    def service(self):
        return ProgramBase._service

    def duplicate_sheet(self, program_name: str, spreadsheet_id: str):
        new_spreadsheet = self._g_sheet.copy(
            spreadsheet_id,
            title=f"[Test] - Root Program:: {program_name.capitalize()} {date.today()}",
            copy_permissions=True,
            folder_id="1rdON9vpywCPYp_a_gwxzOciYVQm1DdyR"
        )
        return new_spreadsheet.id

    def find_sheet_id(self, sheet_name: str):
        sheet_id = self._g_sheet.worksheet(
            sheet_name
        )._properties['sheetId']
        return sheet_id

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
    
    ### --- API Requests --- ###

    def run_requests(
        self, 
        requests:list
    ):
        
        # Create a batch request to apply both actions
        batch_update_request = {
            'requests': requests
        }
        res = self._g_sheet.batch_update(batch_update_request)
        return(res)
    
    @staticmethod
    def get_clear_validation_req(
        sheet_id:int,
        start_row:int, 
        end_row:int,
        start_col:int,
        end_col:int
    ):
        req = {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    'startRowIndex': start_row,
                    'endRowIndex': end_row,
                    'startColumnIndex': start_col,
                    'endColumnIndex': end_col
                },
                "cell": {
                    "dataValidation": None  # This clears data validation (dropdown)
                },
                "fields": "dataValidation"
            }
        }
        return(req)

    @staticmethod
    def get_merge_request(
        sheet_id:int,
        start_row:int, 
        end_row:int,
        start_col:int,
        end_col:int
    ):
        req = {
            'mergeCells': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': start_row,
                    'endRowIndex': end_row,
                    'startColumnIndex': start_col,
                    'endColumnIndex': end_col
                },
                'mergeType': 'MERGE_ALL'
            }
        }
        return(req)

    @staticmethod
    def get_bg_colour_request(
        sheet_id:int,
        start_row:int, 
        end_row:int,
        start_col:int,
        end_col:int,
        colour:dict,
        include_borders:bool
    ):
        assert all([k in colour.keys() for k in ["red", "green", "blue"]]), \
            "Red, green and blue colour keys must be given in the colour parameter"
        
        if include_borders:
            repeat_cell = {   
                    'userEnteredFormat': {
                        'backgroundColor': colour,
                        'borders': {
                            'top': {
                                'style': 'SOLID',
                                'width': 1,
                                'color': colour
                            },
                            'bottom': {
                                'style': 'SOLID',
                                'width': 1,
                                'color': colour
                            },
                            'left': {
                                'style': 'SOLID',
                                'width': 1,
                                'color': colour
                            },
                            'right': {
                                'style': 'SOLID',
                                'width': 1,
                                'color': colour
                            }
                        }
                    }
                }
            fields = 'userEnteredFormat(backgroundColor,borders)'
        else:
            repeat_cell = {   
                    'userEnteredFormat': {
                        'backgroundColor': colour,
                    }
                }
            fields = 'userEnteredFormat.backgroundColor'
        
        req = {
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': start_row,
                    'endRowIndex': end_row,
                    'startColumnIndex': start_col,
                    'endColumnIndex': end_col
                },
                'cell': repeat_cell,
                'fields': fields
            }
        }
        return(req)
    
    def merge_cells(
        self,
        sheet_id:int,
        start_row:int,
        end_row:int,
        start_col:int,
        end_col:int,
        colour:dict={"red":1, "green":0.976, "blue":0.905},
        remove_data_validation=True,
        new_value=None,
        sheet_name=None,
        colour_borders=False
    ):
        
        assert (not new_value) or (new_value and sheet_name)

        ### --- Handle Data Validation --- ###

        # Clear dropdowns (data validation rules) in the range to be merged
        clear_data_validation_req = self.get_clear_validation_req(
            sheet_id,
            start_row,
            end_row,
            start_col,
            end_col
        )

        ### --- Handle Background Colour Adjustment --- ###

        # Define the request to change the background color
        colour_request = self.get_bg_colour_request(
            sheet_id,
            start_row,
            end_row,
            start_col,
            end_col,
            colour,
            include_borders=colour_borders
        )

        ### --- Handle Cell Merging --- ###

        # Define the request to merge cells
        merge_request = self.get_merge_request(
            sheet_id,
            start_row,
            end_row,
            start_col,
            end_col
        )

        if remove_data_validation:
            requests = [
                clear_data_validation_req,
                colour_request,
                merge_request
            ]
        else:
            requests = [
                colour_request,
                merge_request
            ]

        res = self.run_requests(
            requests=requests
        )
        
        # Edit the top left cell if requested
        if new_value:
            self._g_sheet.worksheet(
                sheet_name
            ).update_cell(start_row+1, start_col+1, new_value)
        return(res)