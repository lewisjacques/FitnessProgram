from gspread_dataframe import set_with_dataframe
from datetime import datetime, timedelta
from pandas import DataFrame

import calendar
import re

from month import Month
from program_base import ProgramBase


class Sheet(ProgramBase):
    def __init__(
        self, 
        program_name:str, 
        spreadsheet_id:str, 
        duplicate:bool, 
        verbose:bool,
        sheet_names:list[str],
        clean_parsed_months:bool
        ):

        super().__init__(spreadsheet_id)

        # If run as a duplicate run updates on a copy of the sheet for testing
        if duplicate:
            print(f"\n\tDuplicating program: {program_name.capitalize()}")
            spreadsheet_id = self.duplicate_sheet(program_name, spreadsheet_id)
            print(f"\tNew sheet Link: https://docs.google.com/spreadsheets/d/{spreadsheet_id}", end="\n\n")
            # Reinitialise ProgramBase for the duplicated sheet
            super().__init__(spreadsheet_id)

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

        # Retrieve all merge ranges for all sheets
        self.merged_ranges = self.retrieve_all_merge_ranges()

        # Initialise month-instances dictionary
        self.month_instances = dict()
        self.parse_months(parse_sheets, clean_parsed_months, verbose)
    
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

    def parse_months(
        self, 
        parse_sheets:tuple[str], 
        clean_parsed_months:bool,
        verbose:bool=False
    ):
        """
        Parse months that are using the new format where exercise notes
        are stated explicitly next to the exercise rather than in the comment
        of the cell with the exercise

        Args:
            explicit_format_months (list): List of months using the new methodology
            where each element of the list represents a sheet tab
        """

        for month_sheet_name in parse_sheets:
            print(f"\t\tParsing Sheet: {month_sheet_name}")
            # Get raw month data
            month_data = self.g_sheet.worksheet(month_sheet_name).get_all_values()
            # Get merged ranges for this sheet
            month_merged_ranges = self.merged_ranges[month_sheet_name]

            month_instance = Month(
                data=month_data,
                spreadsheet_id=self.spreadsheet_id,
                sheet_name=month_sheet_name,
                merged_ranges=month_merged_ranges
            )

            ### --- Clean Month Sheets By Merging Unused Cells --- ###

            if clean_parsed_months:
                # Clean the months by merging unused cells and prettifying the program
                month_instance.clean_sessions()

            # month instances haven't been added to yet
            if self.month_instances == {}:
                # month_instances needs properly initialising
                self.month_instances = {
                    month_sheet_name: month_instance
                }
            else:
                self.month_instances[month_sheet_name] = month_instance
        return
    
    def add_new_month(self, new_month:datetime, clean=True):
        print(f"\n\tAdding New Month: {new_month.strftime('%b %y')}")
        all_sheets = [s.title for s in self.g_sheet.worksheets()]
        
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

        # Add it to the month_instances dictionary to get month_instances variables
        self.parse_months([new_month_meta["sheet_name"]])

        if clean:
            # Clean sheet
            self.clean_new_month(sheet_name=new_month_meta["sheet_name"])

        return

    @staticmethod
    def get_week_number(date:datetime):
        # Get the first day of the month
        first_day = date.replace(day=1)
        # Find the first Sunday of the month
        first_sunday = first_day + timedelta(days=(6 - first_day.weekday()) % 7)
        # Calculate the difference in days between the first Sunday and the given date
        days_difference = (date - first_sunday).days
        # Calculate the week number
        week_number = days_difference // 7 + 1 if days_difference >= 0 else 1
        return week_number
    
    def clean_new_month(self, sheet_name:str):
        month_inst = self.month_instances[sheet_name]

        ### ---  Remove unnecessary pre days --- ###

        # Use the location of first day and length of sessions to merge first week cells
        session_length = month_inst.session_length

        first_session_col = 1
        first_session_row = 3 # Merge the date cell too
        final_session_row = session_length + 3
        final_session_col = month_inst.day1_column_index

        self.gsar.merge_cells(
            sheet_id=month_inst.sheet_id,
            start_row=first_session_row,
            end_row=final_session_row,
            start_col=first_session_col,
            end_col=final_session_col,
            colour={"red":1, "green":0.976, "blue":0.905},
            remove_data_validation=False,
            new_value=" ",
            sheet_name=sheet_name,
            colour_borders=True
        )

        ### --- Remove Unnecessary Post Days --- ###

        ## -- Remove End of Final Week -- ##

        # Get the datetime object for the month given the sheet name
        month_dt_obj = datetime.strptime(month_inst.sheet_name, "%b %y")
        # Get the final day of the month
        month_final_day = calendar.monthrange(month_dt_obj.year, month_dt_obj.month)[1]
        # Set the date to the final day of the month for efficiency below
        month_final_day_dt_obj = month_dt_obj.replace(day=month_final_day)
        # Get the week number of the final day so we can find the row number it sits on
        final_week_number = self.get_week_number(month_final_day_dt_obj)
        fw_row_number = (final_week_number*session_length) + 4

        # If final day is a Saturday, no cells to merge this month
        if month_final_day_dt_obj.weekday() != 5:
            final_session_col = month_inst.find_dayx(row_num=fw_row_number, day_num=month_final_day)
            
            self.gsar.merge_cells(
                sheet_id=month_inst.sheet_id,
                start_row=fw_row_number-1,
                end_row=fw_row_number+session_length-1, # 0 indexed rows
                start_col=final_session_col+2, # We want to merge the day after the final day
                end_col=15, # Always going to be the right-most column
                colour={"red":1, "green":0.976, "blue":0.905},
                remove_data_validation=False,
                new_value=" ",
                sheet_name=sheet_name,
                colour_borders=True
            )

        ## -- Remove Remaining Whole Weeks -- ##

        # Set current week to be the week after the final week row number
        current_row_number = fw_row_number + session_length - 1
        while current_row_number < 54:
            self.gsar.merge_cells(
                sheet_id=month_inst.sheet_id,
                start_row=current_row_number,
                end_row=current_row_number+session_length,
                start_col=1,
                end_col=15, # Always going to be the right-most column
                colour={"red":1, "green":0.976, "blue":0.905},
                remove_data_validation=False,
                new_value=" ",
                sheet_name=sheet_name,
                colour_borders=True
            )
            current_row_number += session_length + 1

        return
    
    def retrieve_all_merge_ranges(self) -> dict:
        # Retrieve the full spreadsheet metadata
        sheet_metadata = self.service.spreadsheets().get(
            spreadsheetId=self.spreadsheet_id, 
            fields='sheets'
        ).execute()
        sheets = sheet_metadata['sheets']

        # Get merged ranges for the specific sheet by name
        merged_ranges = {
            s['properties']['title'] : s.get('merges', []) \
                for s in sheets
        }
        return(merged_ranges)