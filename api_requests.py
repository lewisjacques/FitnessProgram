from gspread import Spreadsheet

class GoogleSheetsAPIRequests:
    def __init__(self, gspread_sheet_instance:Spreadsheet):
        self.g_sheet = gspread_sheet_instance
        return
    
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

        print(f"\t\tMerging cells: ({start_row},{start_col}) -> ({end_row}, {end_col})")

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