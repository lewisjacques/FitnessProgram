from session  import Session
from datetime import datetime
import re

class Month:
    def __init__(self, month_values:list):
        """
        Obect to store every element of a given month of training

        Args:
            month_values (list): List of lists for all values on a given sheet
                (this method prevents having to pass an gspread instance between classes)
        """
        self.month_values = month_values
        # Find where day 1 starts in this given month
        day1_column_index = self.find_day1()
        # Get month header in the sheet
        self.month = self.get_month()

        # Fine the session length for day 1, assume same session length throughout month
        self.session_length = self.find_session_length(day1_column_index)
        self.month_sessions = self.build_sessions(day1_column_index)

        # Get exercises per session
        self.total_sessions = sum([1 for s in self.month_sessions if s.is_valid])
        session_lengths = [s.total_ex for s in self.month_sessions]
        self.ex_per_session = sum(session_lengths)/len(session_lengths)

        # Get sessions per week
        total_days = len(self.month_sessions)
        total_weeks = total_days/7
        self.sessions_per_week = self.total_sessions/total_weeks
        
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
        month = re.findall("(\w* \d{4})", month_cell_value)[0]
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
        for row_index in range(3,53,self.session_length):
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
        session_vals = {"Session Title": session_title}
        for row in range(session_anchor[0]+1, session_anchor[0]+self.session_length):
            exercise = self.month_values[row][session_anchor[1]]
            outcome = self.month_values[row][session_anchor[1]+1]

            if exercise == "":
                try:
                    session_vals[exercise] += 1
                # One empty exercise encountered already
                except KeyError:
                    session_vals[exercise] = 1
            else:
                session_vals[exercise] = outcome
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