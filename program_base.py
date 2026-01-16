from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from datetime import date
from functools import cached_property
import gspread

class ProgramBase:
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    CREDENTIALS_PATH = 'credentials/sa_program_update.json'

    # Shared state
    _gc = None
    _initialized = False
    _service = None
    _creds = None
    _current_spreadsheet_id = None  # Track the active spreadsheet_id at class level
    
    # Class-level caches shared across all instances
    _g_sheet_cache = {}  # Cache g_sheet objects per spreadsheet_id
    _worksheets_cache = {}  # Cache all worksheets list per spreadsheet_id
    _worksheet_dict_cache = {}  # Cache worksheets as dict {name: worksheet} per spreadsheet_id

    def __init__(self, spreadsheet_id:str, refresh_sheet:bool=True):
        # Initialize instance-level cache for sheets by name
        self._sheet_cache = {}
        self._merge_ranges_cache = None
        
        # Only initialize shared state once
        if not ProgramBase._initialized:
            creds = self.verify_user()
            ProgramBase._creds = creds
            self.init_class_variables(spreadsheet_id)

        # Check if spreadsheet_id is changing at class level
        spreadsheet_id_changed = ProgramBase._current_spreadsheet_id != spreadsheet_id
        
        if spreadsheet_id_changed:
            # Clear instance caches when switching spreadsheets
            self._sheet_cache.clear()
            self._merge_ranges_cache = None
        
        # Update the active spreadsheet_id
        ProgramBase._current_spreadsheet_id = spreadsheet_id
        self._spreadsheet_id = spreadsheet_id

    # Modify class level specific variables, not instance level
    @classmethod
    def init_class_variables(cls, spreadsheet_id:str):
        """
        Initialize the shared class-level variables. Called on
        ProgramBase rather than cls to avoid writing variables
        to the subclass instance
        """
        print("Initialising class variables")
        ProgramBase._initialized = True
        ProgramBase.spreadsheet_id = spreadsheet_id

        # Service object to apply conditional formatting
        ProgramBase._service = build('sheets', 'v4', credentials=ProgramBase._creds)
        # Authorise Google Cloud access
        ProgramBase._gc = gspread.authorize(ProgramBase._creds)

    def init_sheet(self, spreadsheet_id:str):
        """
        Refresh Worksheet for provided spreadsheet ID
        """
        # Initialise google sheet instance
        print("Refresh gspread spreadsheet instance")
        return(self.gc.open_by_key(spreadsheet_id))
    
    @property
    def spreadsheet_id(self):
        return self._spreadsheet_id
    
    @property
    def g_sheet(self):
        """Get or create cached g_sheet for this spreadsheet_id."""
        sid = self.spreadsheet_id
        if sid not in ProgramBase._g_sheet_cache:
            print(f"Loading g_sheet for {sid}")
            ProgramBase._g_sheet_cache[sid] = self.init_sheet(sid)
        return ProgramBase._g_sheet_cache[sid]
    
    @property
    def service(self):
        return ProgramBase._service
    
    @property
    def gc(self):
        if ProgramBase._gc is None:
            raise ValueError("Google Sheets client (_gc) has not been initialized. Ensure init_class_variables() was called.")
        return ProgramBase._gc
    
    @property
    def worksheets(self):
        """
        Returns cached worksheets list for the current spreadsheet ID.
        Shared across all instances of the same spreadsheet.
        """
        sid = self.spreadsheet_id
        if sid not in ProgramBase._worksheets_cache:
            ws_list = self.g_sheet.worksheets()
            ProgramBase._worksheets_cache[sid] = ws_list
            # Also build the dict cache for fast lookups
            ProgramBase._worksheet_dict_cache[sid] = {ws.title: ws for ws in ws_list}
        return ProgramBase._worksheets_cache[sid]
    
    def get_worksheets(self):
        """Backward compatibility wrapper for worksheets property."""
        return self.worksheets
    
    def get_sheet_titles(self) -> list[str]:
        """
        Get list of all worksheet titles in the spreadsheet.
        
        Returns:
            list[str]: List of worksheet title strings
        """
        return [s.title for s in self.worksheets]
    
    def get_sheet(self, sheet_name: str):
        """
        Get a worksheet by name from the cached worksheet dictionary.
        Ensures worksheets are cached first, then retrieves from cache.
        
        Args:
            sheet_name (str): Name of the worksheet to retrieve
            
        Returns:
            gspread.Worksheet: The requested worksheet object
        """
        # Ensure worksheets are cached (this builds the dict cache too)
        _ = self.worksheets
        
        sid = self.spreadsheet_id
        ws_dict = ProgramBase._worksheet_dict_cache.get(sid, {})
        
        if sheet_name in ws_dict:
            return ws_dict[sheet_name]
        else:
            # Fallback if not in cache (shouldn't happen if worksheets are cached)
            return self.g_sheet.worksheet(sheet_name)

    def invalidate_worksheet_cache(self, sheet_name: str = None):
        """
        Invalidate cached worksheet references when sheets are modified.
        
        Args:
            sheet_name (str, optional): Specific sheet name to invalidate. 
                                       If None, invalidates all sheets for this spreadsheet.
        """
        sid = self.spreadsheet_id
        if sheet_name is None:
            # Clear all caches for this spreadsheet
            if sid in ProgramBase._worksheets_cache:
                del ProgramBase._worksheets_cache[sid]
            if sid in ProgramBase._worksheet_dict_cache:
                del ProgramBase._worksheet_dict_cache[sid]
            self._sheet_cache.clear()
            print(f"Invalidated all worksheet caches for {sid}")
        else:
            # Invalidate specific worksheet
            if sid in ProgramBase._worksheet_dict_cache:
                if sheet_name in ProgramBase._worksheet_dict_cache[sid]:
                    del ProgramBase._worksheet_dict_cache[sid][sheet_name]
            if sheet_name in self._sheet_cache:
                del self._sheet_cache[sheet_name]
            print(f"Invalidated worksheet cache for: {sheet_name}")
    
    def invalidate_merge_ranges_cache(self):
        """
        Invalidate cached merge ranges when sheets are modified.
        """
        self._merge_ranges_cache = None
        print(f"Invalidated merge ranges cache for {self.spreadsheet_id}")

    def duplicate_sheet(self, program_name: str, spreadsheet_id: str):
        new_spreadsheet = self.gc.copy(
            spreadsheet_id,
            title=f"[Test] - Root Program:: {program_name.capitalize()} {date.today()}",
            copy_permissions=True,
            folder_id="1rdON9vpywCPYp_a_gwxzOciYVQm1DdyR"
        )
        return new_spreadsheet.id

    def find_sheet_id(self, sheet_name:str, pre_processed:bool, spreadsheet_id:str):
        """
        Get the sheet ID for a given sheet name.
        Always uses the cached g_sheet to avoid redundant API calls.
        """
        # Use the cached g_sheet property - works for both pre_processed and non-pre_processed
        sheet_id = self.g_sheet.worksheet(sheet_name)._properties['sheetId']
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
    
    def retrieve_all_merge_ranges(self) -> dict:
        """
        Retrieve merged cell ranges for all sheets in the spreadsheet.
        Results are cached to avoid repeated metadata API calls.
        
        Returns:
            dict: Dictionary mapping sheet names to their merge ranges
        """
        if self._merge_ranges_cache is None:
            # Retrieve the full spreadsheet metadata
            sheet_metadata = self._service.spreadsheets().get(
                spreadsheetId=self._spreadsheet_id, 
                fields='sheets'
            ).execute()
            sheets = sheet_metadata['sheets']

            # Get merged ranges for all sheets by name
            self._merge_ranges_cache = {
                s['properties']['title'] : s.get('merges', []) \
                    for s in sheets
            }
        else:
            print(f"Using cached merge ranges for spreadsheet: {self.spreadsheet_id}")
        
        return self._merge_ranges_cache

    def retrieve_merge_ranges_for_sheets(self, sheet_names: list) -> dict:
        """
        Retrieve merged cell ranges only for specified sheets.
        Filters the full merge ranges to only include requested sheets.
        
        Args:
            sheet_names (list): List of sheet names to retrieve merge ranges for
            
        Returns:
            dict: Dictionary mapping sheet names to their merge ranges (only for requested sheets)
        """
        # Get all merge ranges first
        all_ranges = self.retrieve_all_merge_ranges()
        
        # Filter to only requested sheets
        filtered_ranges = {
            name: all_ranges.get(name, [])
            for name in sheet_names
            if name in all_ranges
        }
        
        return filtered_ranges
    
    ### --- API Requests --- ###

    def run_requests(
        self, 
        requests:list
    ):
        
        # Create a batch request to apply both actions
        batch_update_request = {
            'requests': requests
        }
        res = self.g_sheet.batch_update(batch_update_request)
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
            self.g_sheet.worksheet(
                sheet_name
            ).update_cell(start_row+1, start_col+1, new_value)
        return(res)