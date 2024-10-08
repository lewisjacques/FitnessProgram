from oauth2client.service_account import ServiceAccountCredentials

from gspread_dataframe import set_with_dataframe
from datetime import datetime, timedelta
from pandas import DataFrame
import gspread
from datetime import date
import re

from month import Month

class Sheet:

    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    CREDENTIALS_PATH = 'credentials/sa_program_update.json'

    def __init__(
        self, 
        program_name:str, 
        sheet_id:str, 
        duplicate:bool, 
        verbose:bool,
        sheet_names:list[str]
        ):

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

        ### --- Parse New Format Months --- ###

        assert type(sheet_names) == list, \
           f"Please provide sheet_names separated by spaces. Given: {sheet_names}"

        # Get sheets with implicit name (Any month that has YY format) to be parsed
        explicit_format_months = [
            s.title for s in self.g_sheet.worksheets() \
                if re.search(" \d{2}", str(s.title)) is not None
        ]
        
        # Check input tab names
        assert all([s in ("all", *explicit_format_months) for s in sheet_names]),\
            "Some sheet names provided not found in program"
        
        # Set which worksheets to parse
        if sheet_names == ['all']:
            parse_sheets = explicit_format_months
        else:
            parse_sheets = sheet_names

        self.month_instances = self.parse_months(parse_sheets, verbose)

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

    def parse_months(self, parse_sheets:tuple[str], verbose:bool):
        """
        Parse months that are using the new format where exercise notes
        are stated explicitly next to the exercise rather than in the comment
        of the cell with the exercise

        Args:
            explicit_format_months (list): List of months using the new methodology
            where each element of the list represents a sheet tab
        """

        month_instances = {}
        for month_sheet_name in parse_sheets:
            print(f"\tParsing Sheet: {month_sheet_name}")
            month_data = \
                self.g_sheet.worksheet(month_sheet_name).get_all_values()

            month_instance = Month(
                data=month_data,
                g_sheet=self.g_sheet,
                sheet_name=month_sheet_name,
                verbose=verbose
            )
            month_instances[month_sheet_name] = month_instance
            
        return(month_instances)
    
    def duplicate_sheet(self, program_name:str, sheet_id:str):
        new_spreadsheet = self.gc.copy(
            sheet_id, 
            title=f"[Test] - Root Program:: {program_name.capitalize()} {date.today()}", 
            copy_permissions=True,
            folder_id="1rdON9vpywCPYp_a_gwxzOciYVQm1DdyR"
        )

        return(new_spreadsheet.id)
    
    def add_new_month(self, all_months, clean=True):
        all_sheets = [s.title for s in self.g_sheet.worksheets()]





        # Always be one month ahead, so check if an empty month doesn't exist
        # not any([]) returns True to add the first month

        # current_month = []
        # if not any([month_inst.total_sessions == 0 \
        #             for month_inst in all_months
        #     ]) #! Latest month doesn't exist:









        explicit_format_month_sheets = [
            datetime.strptime(s, '%b %y') for s in all_sheets \
                if re.search(" \d{2}", s) is not None
        ]
        # If no new format months add the current month
        if explicit_format_month_sheets == []:
            new_month = datetime.now()
        else:
            # Add 5 weeks to guarentee we're in the next month and then take month, year
            new_month = max(explicit_format_month_sheets).replace(day=1) + timedelta(weeks=5)









        new_month = datetime.now()
        print(new_month.strftime("%b %y"))
        new_month_meta = {
            "sheet_name": new_month.strftime("%b %y"),
            "month_datetime": new_month,
        }

        # Duplicate template
        template_ws = self.g_sheet.worksheet('TEMPLATE')
        template_ws.duplicate(
            insert_sheet_index=len(all_sheets), 
            new_sheet_name=new_month_meta["sheet_name"]
        )

        # Initialise duplicated sheet
        new_ws = self.g_sheet.worksheet(new_month_meta["sheet_name"])
        print("New ws initialised")
        # Find what day the start of the month is and update day 1 accordingly
        # other Month days will follow through
        first_day = new_month.replace(day=1).weekday()
        # Map weekdays to  column values
        day_mapping = {
            # Weekday index : column index in template
            0: "D", # Monday
            1: "F", # Tuesday
            2: "H", # Wednesday
            3: "J", # Thursday
            4: "L", # Friday
            5: "N", # Saturday
            6: "B", # Sunday
        }

        # Set day 1
        new_ws.update(f"{day_mapping[first_day]}4", 1)
        # Give the template a title
        new_ws.update("B2", new_month.strftime("%B %Y"))
        # Give the template weeknumbers
        new_ws.update("A5", int(new_month.replace(day=1).strftime("%V")))

        if clean:
            # Clean sheet
            self.clean_new_month(new_ws, new_month_meta)

        return
    
    def clean_new_month(self, ws:gspread.worksheet.Worksheet, new_month_meta:dict):
        print(f"Running clean_new_month for {new_month_meta['sheet_name']}")

        ### ---  Remove unnecessary pre days --- ###

        # Get raw values for the empty new sheet so the sessions can pull cell locations
        new_month_data = self.g_sheet.worksheet(
            new_month_meta['sheet_name']
        ).get_all_values()

        new_month_instance = Month(
            data=new_month_data,
            g_sheet=self.g_sheet,
            sheet_name=new_month_meta['sheet_name'],
            verbose=True
        )

        

        for s in new_month_instance.month_sessions:
            print(s.print_session_info())
        # print(month_instance.month_values)



















#         # Mapping of weekday to right-most session column index
#         pinch_punch_mapping = {
#             6: 2,  # "Sun"
#             0: 4,  # "Mon"
#             1: 6,  # "Tue"
#             2: 8,  # "Wed"
#             3: 10, # "Thur"
#             4: 12, # "Fri"
#             5: 14  # "Sat"
#         }

#         # Get the column containing the first day
#         day_1_weekday = new_month_meta["month_datetime"].replace(day=1).weekday()
#         # Left most column so -1
#         day_1_col_ind = pinch_punch_mapping[day_1_weekday] - 1

#         session_length = Month.find_session_length(
#             day_1_col_ind,
#             ws.get_all_values()
#         )
#         print(session_length)
#         # Lowest empty row
#         final_ex_row = session_length+4

#         # Rightmost empty column
#         rightmost_col = pinch_punch_mapping[day_1_weekday-1] + 1

#         print(f"Merging from (2,5):({rightmost_col},{final_ex_row})")

        ### --- Remove Unnecessary Post Days --- ###

        
        exit()

        # Merge days that don't exist
        return

    


















    def clean_sessions(self):
        # For each month
            # For each session earlier than today
                # If empty or REST, ILL, HOLIDAY INJURED in keys
                    # Set first exercise to relevant off day
                    # Merge all exercise slots
                # Else if title is only the date (not parsed)
                    # For each exercise
                        # If value == "" (exercise not complete) ----- OPTIONAL becacuse might need reordering
                            # Set exercise to ""
                    # Get first empty session index
                    # Clear dropdown
                    # Colour cell
                    # Merge to the last exercise

        for month_name, month_inst in self.month_instances.items():
            print(month_name, month_inst)
            #! month_inst.clean_month()

        return