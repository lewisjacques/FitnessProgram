from program_base import ProgramBase

from session  import Session
from datetime import datetime
import re

class Month(ProgramBase):
    def __init__(
            self, 
            data:list, 
            spreadsheet_id:str,
            sheet_name:str,
            merged_ranges:dict,
            pre_processed=True
        ):
        """
        Obect to store every element of a given month of training

        Args:
            month_values (list): List of lists for all values on a given sheet
                (this method prevents having to pass a gspread instance between classes)
        """
        # Initialise ProgramBase variables and credentials (actually pulls already initialised class)
        super().__init__(spreadsheet_id, refresh_sheet=False)

        self.month_values = data
        self.sheet_name = sheet_name

        # Find the tab-specific sheet ID using ProgramBase.find_sheet_id
        self.sheet_id = self.find_sheet_id(sheet_name, pre_processed, spreadsheet_id)
        
        # Assign merged ranges
        self.merged_ranges = merged_ranges

        # Find where day 1 starts in this given month
        self.day1_column_index = self.find_dayx(day_num=1, row_num=4)
        # Get month header in the sheet
        self.month = self.get_month()

        # Find the session length for day 1, assume same session length throughout month
        self.session_length = Month.find_session_length(
            self.day1_column_index, 
            self.month_values
        )

        # Expect formatted month values
        if pre_processed:
            self.month_sessions = self.build_sessions(
                self.day1_column_index
            )
        else:
            self.month_sessions = None

        #! self.get_month_meta_data()

    # Set name of class so we can see cleaner output in the terminal
    def __repr__(self):
        return(f"#MI{self.sheet_name.replace(' ', '')}")

    def find_dayx(self, day_num:int=1, row_num:int=4):
        """
        Iterate through columns to find day 'day_num' and locate the
        session boundaries of the sheet for that day

        Raises:
            Exception: If day x not identified
        """
        # Searching 
        skip_col_a = True
        day_x_column_index = None
        # row_num 0 index
        for col_ind, col_val in enumerate(self.month_values[row_num-1]):
            # Skip column A to avoid week numbers
            if skip_col_a:
                skip_col_a = False
                continue

            # When the first day of the month is found "1" or "1 - ___"
            if re.search(f"{day_num}( - )?", col_val) is not None:
                day_x_column_index = col_ind
        
        if day_x_column_index is None:
            # Convert to custom exception class in future
            raise Exception(f"Column for day, {day_num}, not identified in row, {row_num}")
        
        return(day_x_column_index)
    
    def get_month(self):
        """
        Get sheet header containing the month
        """
        month_cell_value = self.month_values[1][1]
        try:
            month = re.findall("(\w* \d{4})", month_cell_value)[0]
        except IndexError:
            raise Exception(f"No month title found, has this sheet been copied manually or edited? {month_cell_value}")
        month_formatted = datetime.strptime(month, '%B %Y').strftime("%Y-%m")
        return(month_formatted)

    def find_session_length(day_1_column_index:int, month_vals:list):
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
        for row_ind, row_vals in enumerate(month_vals):
            if row_ind < 3:
                continue

            if re.search("8( - )?", row_vals[day_1_column_index]) is None:
                session_length += 1
            else:
                return(session_length)
        # Convert to custom exception class in future
        raise Exception("Date headers invalid for matching")
    

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
        #   "Session Title",
        #   "meta",
        # }
        s_data = self.get_session_values(session_anchor=starting_coords)
        session = Session(
            session_data=s_data,
            session_length=self.session_length,
            month=self.month
        )

        # If no session at first position the row is empty. 
        # # (Not is_valid as a REST would not be valid)
        if session.status["is_none"]:
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

            # If we reach an invalid session
            if s_data is None:
                # Assume we're at the end of valid sessions for the week
                break
            
            session = Session(
                session_data=s_data,
                session_length=self.session_length,
                month=self.month
            )
            column_increment+=1
            if not session.status["is_none"]:
                row_sessions.append(session)

        return(row_sessions)
    
    def build_sessions(self, day_1_column_index:int):
        """
        Starting from Day 1, slice the list of lists so each Session can be stored
        as it's own object

        Args:
            day_1_column_index (int): Index containing day 1 for the first row
        """

        all_sessions = []
        # Every row that contains a date
        for row_index in range(3,(9+(5*self.session_length)), self.session_length):
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
        Get slice of the given month for a requested session anchor (top
        left cell of a session)

        Args:
            session_anchor (tuple): top left (row,col) index of the session

        Returns:
            dict: exercise:details key values
        """

        session_title = self.month_values[session_anchor[0]][session_anchor[1]]
        
        # If no session title, not a valid session
        if re.sub(r"\s+", "", session_title) == "":
            return(None)

        try:
            session_day = re.findall("\d{1,2}", session_title)[0]
        except IndexError:
            print(f"Session day not found from:.{session_title}.")
            raise IndexError
        
        session_vals = {
            "Session Title": session_title,
            "meta": {
                "date": datetime.strptime(f"{session_day} {self.sheet_name}", "%d %b %y"),
                "empty_exercise_range": dict(),
                "session_anchor": session_anchor
            }
        }

        ## -- Handle Finding Empty Session Cells -- ##

        empty_sessions = False
        # For each row in the session
        for row in range(session_anchor[0]+1, session_anchor[0]+self.session_length):
            # Extract the exercise from the row
            exercise = self.month_values[row][session_anchor[1]]
            # Extract the outcome from the row
            outcome = self.month_values[row][session_anchor[1]+1]

            if exercise == "":
                # One empty exercise encountered already
                if "" in session_vals.keys():
                    # Count the empty exercises
                    #! Convert these keys to "empty"
                    session_vals[""] += 1
                else:
                    # Record first empty exercise
                    #! Convert these keys to "empty"
                    session_vals[""] = 1
                    # Record that this session has at least one empty sessio
                    empty_sessions = True
                    # As this is the first empty exercise set the top left
                    # cell to be the 'cell achor' for the empty cells to merge
                    session_vals["meta"]["empty_exercise_range"].update(
                        {"start": (row, session_anchor[1])}
                    )
            else:
                # Otherwise just append the exercise,outcome key-values to session vals
                session_vals[exercise] = outcome
        
        # If at least one empty sessio
        if empty_sessions:
            # Set the bottom right cell of empty cells to merge
            session_vals["meta"]["empty_exercise_range"].update(
                {"end": (
                    session_anchor[0]+self.session_length-1, 
                    session_anchor[1]+1
                )}
            )

        return(session_vals)
    
    def get_month_meta_data(self, verbose):
        self.total_sessions = sum([1 for s in self.month_sessions if s.status["is_valid"]])
        if self.total_sessions != 0:
            # Get exercises per session
            session_lengths = [s.total_ex for s in self.month_sessions if s.status["is_valid"]]

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

    def cell_in_range(self, merge_range, row, col):
        start_row = merge_range['startRowIndex']
        end_row = merge_range['endRowIndex']
        start_col = merge_range['startColumnIndex']
        end_col = merge_range['endColumnIndex']
        
        if start_row <= row < end_row and start_col <= col < end_col:
            return True
        return False

    #! Move to session.py to give an status["is_merged"] value
    def get_merge_status(self, session: Session):
        """Determine if the session has been processed based on merged cells."""
        session_start_row = session.session_anchor[0]
        session_start_col = session.session_anchor[1]
        session_end_row = session_start_row + self.session_length
        session_end_col = session_start_col + 2  # Assuming a single-column session width

        for merge_range in self.merged_ranges:
            # Check if the session range overlaps with the merge range
            if (merge_range['startRowIndex'] <= session_end_row and
                merge_range['endRowIndex'] > session_start_row and
                merge_range['startColumnIndex'] <= session_end_col and
                merge_range['endColumnIndex'] > session_start_col):

                return True

        print("No overlap found with merged ranges")
        return False

    def clean_sessions(self):
        """
        For each session earlier than today
            If empty or REST, ILL, HOLIDAY INJURED in keys
                Set first exercise to relevant off day
                Merge all exercise slots
            Else if title is only the date (not parsed)
                For each exercise
                    If value == "" (exercise not complete) ----- OPTIONAL becacuse might need reordering
                        Set exercise to ""
                Get first empty session index
                Clear dropdown
                Colour cell
                Merge to the last exercise
                Add session title
        """
        print("\t\t\tCleaning Sessions!")

        for session in self.month_sessions:
            stat_string = ", ".join([k for k,v in session.status.items() if v])
            print(f"\t\t\t\t{session.session_anchor} - {session.date_str} - {stat_string}")
            # Is the session empty?
            empty_session = session.status["is_none"]
            # Is the session before todays date?
            historical_day = session.date < datetime.today()
            # Get merge status for the session
            is_merged = self.get_merge_status(session)

            ## -- Handle Empty Sessions -- ##

            # If we come across a day in the future skip
            if not historical_day:
                print("Not Historical")
                continue
            
            # If an empty session in the past, the day needs cleaning up with "REST"
            if empty_session and historical_day and not is_merged:
                #! Merge the whole day filling in "REST"
                print("Empty session and historical day, merge whole day : REST")
                continue

            ## -- Handle Active Session's Empty Rows -- ##

            # Merge unused exercise slots
            if not is_merged and historical_day and session.status["is_valid"]:
                print(f"Not merged, is historical day and is valid. Merge empty exercises")
                
                self.merge_cells(
                    sheet_id=self.sheet_id,
                    start_row=session.empty_exercise_range["start"][0],
                    end_row=session.empty_exercise_range["end"][0],
                    start_col=session.empty_exercise_range["start"][1],
                    end_col=session.empty_exercise_range["end"][1],
                    colour={"red":1, "green":0.976, "blue":0.905},
                    remove_data_validation=True,
                    new_value="REMOVE THIS PLACEHOLDER",
                    sheet_name=self.sheet_name
                    # colour_borders=True
                )

            ## -- Handle Session Title -- ##

            # If exercise data exists on the day
            # if session.status["is_valid"]:
            #     # Update title name
            #     cur_title = session.title
            #     # If not already formatted
            #     if not re.search(r"\d{{1,2}} - ", cur_title):
            #         muscle_groups = session.muscle_groups

            #         new_title = ", ".join(muscle_groups)
            
        return
    
