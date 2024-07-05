from gspread.client import Spreadsheet

from session  import Session
from datetime import datetime
import re

class Month:
    def __init__(
            self, 
            data:list, 
            g_sheet:Spreadsheet,
            sheet_name:str,
            verbose=False):
        """
        Obect to store every element of a given month of training

        Args:
            month_values (list): List of lists for all values on a given sheet
                (this method prevents having to pass an gspread instance between classes)
        """

        self.month_values = data
        self.sheet_id = g_sheet.worksheet(sheet_name)._properties['sheetId']

        # Find where day 1 starts in this given month
        day1_column_index = self.find_day1()
        # Get month header in the sheet
        self.month = self.get_month()

        # Fine the session length for day 1, assume same session length throughout month
        self.session_length = self.find_session_length(day1_column_index)
        self.month_sessions = self.build_sessions(day1_column_index)

        self.clean_month(
            g_sheet
        )
        self.set_month_meta_data(verbose)

    def find_day1(self):
        """
        Iterate through row 4 to find day 1 so we can subsequently find day 8
        to get hold of the session length

        Raises:
            Exception: If day 1 not identified
        """
        # Searching 
        skip_col_a = True
        day_1_column_index = None
        for col_ind, col_val in enumerate(self.month_values[3]):
            # Skip column A to avoid week numbers
            if skip_col_a:
                skip_col_a = False
                continue

            # When the first day of the month is found "1" or "1 - ___"
            if re.search("1( - )?", col_val) is not None:
                day_1_column_index = col_ind
        
        if day_1_column_index is None:
            # Convert to custom exception class in future
            raise Exception("Day 1 Column not identified")
        
        return(day_1_column_index)
    
    def get_month(self):
        """
        Get sheet header containing the month
        """
        month_cell_value = self.month_values[1][1]
        try:
            month = re.findall("(\w* \d{4})", month_cell_value)[0]
        except IndexError:
            raise Exception("No month title found, has this sheet been copied manually or edited?")
        month_formatted = datetime.strptime(month, '%B %Y').strftime("%Y-%m")
        return(month_formatted)

    def find_session_length(self, day_1_column_index:int):
        """
        Function to find the number of rows in a session for the month.

        Iterate through rows through the column that has day 1 to look for day 8
        to ultimately calculate the number of columns per session. This is important
        if session structure changes month-to-month

        Args:
            day_1_column_index (int)

        Raises:
            Exception: If date headers are invalid for matching
        """
                
        session_length = 0
        for row_ind, row_vals in enumerate(self.month_values):
            if row_ind < 3:
                continue

            if re.search("8( - )?", row_vals[day_1_column_index]) is None:
                session_length += 1
            else:
                return(session_length)
        # Convert to custom exception class in future
        raise Exception("Date headers invalid for matching")
    
    def build_sessions(self, day_1_column_index:int):
        """
        Starting from Day 1, slice the list of lists so each Session can be stored
        as it's own object

        Args:
            day_1_column_index (int): Index containing day 1 for the first row
        """
        all_sessions = []
        # Every row that contains a date
        for row_index in range(3,(9+(5*self.session_length)),self.session_length):
            # First row starts depending on where Sunday falls
            if row_index == 3:
                column_start_index = day_1_column_index
            # All other rows start at index 1
            else:
                column_start_index = 1
            
            # week_sessions holds a session object for every day of that week
            week_sessions = self.row_iterate(
                row_number=row_index,
                column_index_init=column_start_index
            )
            if week_sessions is not None:
                # Concatenate all month sessions
                all_sessions = [*all_sessions, *week_sessions]
        
        return(all_sessions)

    def get_session_values(self, session_anchor:tuple) -> dict:
        """
        Get slice of month for requested session data

        Args:
            session_anchor (tuple): top left (row,col) index of the session

        Returns:
            dict: exercise:details key values
        """

        session_title = self.month_values[session_anchor[0]][session_anchor[1]]
        session_vals = {
            "Session Title": session_title,
            "meta": {
                "empty_exercise_range": dict(),
                "session_anchor": session_anchor
            }
        }
        empty_sessions = False

        for row in range(session_anchor[0]+1, session_anchor[0]+self.session_length):
            exercise = self.month_values[row][session_anchor[1]]
            outcome = self.month_values[row][session_anchor[1]+1]

            if exercise == "":
                if "" in session_vals.keys():
                    session_vals[exercise] += 1
                # One empty exercise encountered already
                else:
                    session_vals[exercise] = 1
                    empty_sessions = True
                    session_vals["meta"]["empty_exercise_range"].update(
                        {"start": (row, session_anchor[1])}
                    )
            else:
                session_vals[exercise] = outcome
        
        if empty_sessions:
            session_vals["meta"]["empty_exercise_range"].update(
                {"end": (
                    session_anchor[0]+self.session_length-1, 
                    session_anchor[1]+1
                )}
            )














            # print(session_vals["meta"]["empty_exercise_range"])

        return(session_vals)

    def row_iterate(self, row_number:int, column_index_init:int=0):
        """        
        Iterate through the row in the program creating Session objects at every other
        column to account for both the exercise name and the corresponding comment to the
        right

        Args:
            row_number (int)
            column_index_init (int, optional): Initialising column index. Defaults to 1.
        """
        
        # Get the first session
        col_val = column_index_init
        starting_coords = (row_number,col_val)

        # s_data keys:
        #   "Session Title"
        #   "empty_exercise_range" optional
        #   exercises
        # }
        s_data = self.get_session_values(session_anchor=starting_coords)
        session = Session(
            session_data=s_data,
            session_length=self.session_length,
            month=self.month
        )

        # If no session at first position the row is empty. 
        # # (Not is_valid as a REST would not be valid)
        if session.is_none:
            return(None)
        else:
            row_sessions = [session]

        column_increment = 1
        # While there are still days in the week or we reach Saturday
        while col_val < 13:
            col_val = column_index_init+(column_increment*2)
            # Top left column of the session
            session_anchor = (row_number, col_val)
            s_data = self.get_session_values(session_anchor=session_anchor)
            
            session = Session(
                session_data=s_data,
                session_length=self.session_length,
                month=self.month
            )
            column_increment+=1
            if not session.is_none:
                row_sessions.append(session)

        return(row_sessions)
    
    def set_month_meta_data(self, verbose):
        self.total_sessions = sum([1 for s in self.month_sessions if s.is_valid])
        if self.total_sessions != 0:
            # Get exercises per session
            session_lengths = [s.total_ex for s in self.month_sessions if s.is_valid]

            self.total_exercises = sum(session_lengths)
            self.total_sessions = len(session_lengths)
            self.ex_per_session = self.total_exercises/self.total_sessions

            # Get sessions per week
            total_days = len(self.month_sessions)
            total_weeks = total_days/7
            self.sessions_per_week = self.total_sessions/total_weeks

        else:
            self.ex_per_session = 0
            self.sessions_per_week = 0
            self.total_exercises = 0
            self.total_sessions = 0
            session_lengths = 0
            total_days = 0
            total_weeks = 0

        if verbose:
            print(f"\t\tSession lengths: {session_lengths}")
            print(f"\t\tTotal days: {total_days}")
            print(f"\t\tTotal weeks: {total_weeks}")
            print(f"\t\tTotal sessions: {self.total_sessions}")
            print(f"\t\tSessions per week: {self.sessions_per_week}")
            print("\n")

    def clean_month(self, g_sheet):
        return








        # Merge unused cells
        for session in self.month_sessions:
            # If data exists on the day
            if not session.is_none:
                # Merge unused exercise slots
                if not session.merged:
                    session.merge_cells(
                        g_sheet,
                        self.sheet_id
                    )

            # If exercise data exists on the day
            if session.is_valid:
                # Update title name
                cur_title = session.title
                # If not already formatted
                if not re.search(r"\d{{1,2}} - ", cur_title):
                    muscle_groups = session.muscle_groups

                    new_title = ", ".join(muscle_groups)
            




        # Colour unused cells
            # Colour top empty cell, merge the rest




        return