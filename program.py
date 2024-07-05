from comment import RawCommentFile

from datetime import datetime, timedelta
from sheet import Sheet
import pandas as pd
import numpy as np
import json
import os
import re

class Program:
    PROGRAM_SPECS_PATH = "program_specs.json"

    def __init__(
            self, 
            program_name:str=None, 
            reparse_legacy:bool=False, 
            verbose=False,
            duplicate=False
        ):
        """
        Class to initialise sheet access and then iteratively parse each month,
        week and session from legacy comments and live Program sheets

        Args:
            program_name (str, optional): Details have to be given in PROGRAM_SPECS. 
                Defaults to None.
            reparse_legacy (bool, optional): If legacy comments need parsing, add flag. 
                Defaults to False.
        """

        ### --- Run Set-Up --- ###

        self.program_specs = json.load(self.PROGRAM_SPECS_PATH)

        print(f"\n### --- Parsing Program: {self.program_specs[program_name]['pretty']} --- ###")

        # Pull out variables for the relevant sheet
        program_specs = self.program_specs[program_name]
        parsed_comment_location = program_specs['parsed_comments']
        legacy_comment_location = program_specs['legacy_comments']
        sheet_id = program_specs['sheet_id']

        # If running the testing program, duplicate by default
        if program_name == "test":
            duplicate = True
        # Initialise sheet access and duplicate sheet if duplicate=True
        self.sheet = Sheet(program_name, sheet_id, duplicate)

        ### --- Get / Generate Archived Comments --- ###

        # Returns None if no data provided
        legacy_exercise_df = self.get_archived_comments(
            parsed_comment_location,
            legacy_comment_location,
            reparse_legacy
        )

        ### --- Parse New Format Months --- ###

        # Get new format months
        explicit_format_months = [
            s.title for s in self.sheet.g_sheet.worksheets() \
                if re.search(" \d{2}", s.title) is not None
        ]
        
        # key: month name, value: Month instance or empty dictionary
        month_sessions = self.sheet.parse_months(
            explicit_format_months,
            verbose=verbose
        )

        # ### --- Combine Legacy and New Format Month Data --- ###

        all_exercise_df = self.concatenate_all_months(
            legacy_exercise_df,
            month_sessions
        )

        # ### --- Enrich Logged Results --- ###

        enriched_logs_df = self.enrich_logs(all_exercise_df)

        # Write newly parsed comments to the sheet
        self.sheet.write_to_sheet(
            df=enriched_logs_df,
            tab_name="Logs (via Python)"
        )

        ### --- Duplicate Month Template Sheet --- ###

        # Always be one month ahead, so check if an empty month exists
        # not any([]) returns True if there's no month instances at all
        if not any([month_inst.total_sessions == 0 for month_inst in month_sessions.values()]):
            print(f"\tAdding new month as the latest has updates")
            self.add_new_month()

        ### --- Program Meta --- ###

        # self.get_program_meta(month_sessions, verbose)

        print("\tComplete\n")

    def get_archived_comments(
        self, 
        parsed_comment_location:str,
        legacy_comment_location:str,
        reparse_legacy:str
    ):
        """
        Either pull the archived comments that have been parsed or if reparse_legacy
        then reparse from the legacy file. Return exercise_df to be appended to by 
        the new format months. Eventually everything will be stored and stable enough
        to make this function legacy

        Args:
            parsed_comment_location (str): File location for parsed file
            legacy_comment_location (str): File location for raw C+P comments from GSheets
            reparse_legacy (str): Flag to reparse the legacy file or not
        """

        if legacy_comment_location is not None:
            # If we need to parse the legacy comments into a readable format
            if parsed_comment_location is None or \
                not os.path.isfile(parsed_comment_location) or \
                reparse_legacy:

                with open(legacy_comment_location) as coms:
                    legacy_comments = ''.join(coms.readlines())

                # Parse the raw comments getting rid of unnecessary information with re
                raw_comments = RawCommentFile(legacy_comments)
                raw_comments.save_to_local(parsed_comment_location)
                exercise_df = raw_comments.parsed_comment_df
            else:
                try:
                    exercise_df = pd.read_csv(parsed_comment_location)
                except FileNotFoundError:
                    print("Parsed legacy file location is given but does not exist")
                    raise FileNotFoundError
            return(exercise_df)
        else: return(None)
    
    def concatenate_all_months(
        self,
        exercise_df:pd.DataFrame, # or None
        month_sessions:dict
    ):
        """
        Concatenate legacy comments with new format months

        Args:
            exercise_df (pd.DataFrame): Legacy exercise data-frame
            month_sessions (dict): month_sheet_name:str, month_instance:Month
        """

        if exercise_df is not None:
            exercise_df = exercise_df.loc[:, [
                "Date",
                "Cell Data",
                "Comment"
            ]].copy()
            exercise_df.rename(columns={
                "Cell Data": "Exercise",
                "Comment": "Result"
            }, inplace=True)
        else:
            exercise_df = pd.DataFrame(columns=[
                "Date",
                "Exercise",
                "Result"
            ])

        # For each month add every valid exercise to the exercise df
        for month_instance in month_sessions.values():
            for session in month_instance.month_sessions:
                # Not empty and not a rest day
                if session.is_valid:
                    for ex, result in session.exercises.items():
                        # Skipped exercise block
                        if ex == "" or ex == "meta":
                            continue

                        exercise_df = pd.concat(
                            [
                                pd.DataFrame({
                                    "Date": session.date,
                                    "Exercise": ex,
                                    "Result": result
                                }, index=[0]),
                                exercise_df
                            ],
                            ignore_index=True
                        )
        
        return(exercise_df.sort_values(["Date"]))
    
    def find_result(self, result):
        """
        Get a rough estimat of the exercise result. Long term this will be an 
        NLP-like system of finding siilar strings

        Args:
            result (float, int, string): Exercise result value
        """

        # If the result was written in kilos
        if 'kg' in str(result):
            kg_value = re.findall(r"([0-9]{1,3}([\.][0-9]{1,2})?)kg", str(result))
            try:
                return(max([float(v[0]) for v in kg_value]))
            except IndexError:
                return(0)
            # Empty kg value
            except ValueError:
                return(0)
            
        # If it's not kilos then look for a value or a time
        else:
            estimated_weight = re.findall(r"([0-9]{1,3}([\.:][0-9]{1,2})?)", str(result))
            if estimated_weight == []:
                return(0)
            else:
                # If any values found are times, take the first one
                if any([":" in v[0] for v in estimated_weight]):
                    t_val = [v[0] for v in estimated_weight if ":" in v[0]]
                    return(t_val[0])
                else:
                    return(max([float(v[0]) for v in estimated_weight]))
            
    def find_status(self, result):
        """
        Find  whether it was a 
            Peak set (1 set of 8+ reps)
            Working set (2+ sets of 8+ reps)
            Static (not given)

        Args:
            result (str): Exercise result
        """
        #! Consolidate regex
        if re.search(r"(working)", str(result).lower()) is not None or \
            re.search(r"(ww)", str(result).lower()) is not None:
            return("Working")
        if re.search(r"(peak)", str(result).lower()) is not None or \
            re.search(r"(pw)", str(result).lower()) is not None:
            return("Peak")
        return("Static")
    
    def enrich_logs(self, all_exercise_df:pd.DataFrame):
        """
        Get accurate estimation of weights lifted

        Args:
            all_exercise_df (pd.DataFrame): Legacy and new format month logged sessions
        """

        # Get kg value, if no kg value find take the next largest number
        all_exercise_df["Weight"] = all_exercise_df["Result"].apply(self.find_result)
        ## - Append set type (Working / Peak / Static, that priority) - ##
        all_exercise_df["Status"] = all_exercise_df["Result"].apply(self.find_status)

        return(all_exercise_df)
    
    def add_new_month(self):
        all_sheets = [s.title for s in self.sheet.g_sheet.worksheets()]
        explicit_format_month_sheets = [
            datetime.strptime(s, '%b %y') for s in all_sheets \
                if re.search(" \d{2}", s) is not None
        ]

        # If no new format months add the first one
        if explicit_format_month_sheets == []:
            new_month = datetime.now()
            new_month_tab_name = new_month.strftime('%b %y')
        else:
            # Add 5 weeks to guarentee we're in the next month and then take month, year
            new_month = max(explicit_format_month_sheets).replace(day=1) + timedelta(weeks=5)
            new_month_tab_name = new_month.strftime("%b %y")

        # Duplicate template
        self.sheet.g_sheet.worksheet('TEMPLATE')\
            .duplicate(insert_sheet_index=len(all_sheets), new_sheet_name=new_month_tab_name)
        
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
        self.sheet.g_sheet.worksheet(new_month_tab_name).update(f"{day_mapping[first_day]}4", 1)
        # Give the template a title
        self.sheet.g_sheet.worksheet(new_month_tab_name).update("B2", new_month.strftime("%B %Y"))
        # Give the template weeknumbers
        self.sheet.g_sheet.worksheet(new_month_tab_name).update("A5", int(new_month.replace(day=1).strftime("%V")))












        # Remove unnecessary pre and post days

        return
    
    def get_program_meta(self, month_sessions:dict, verbose:bool):
        # --- Add Historical Meta Data --- #

        total_sessions = {}
        total_exercises = {}
        exercises_per_session = {}
        sessions_per_week = {}
        
        for month_name, month_inst in month_sessions.items():
            total_sessions[month_name] = month_inst.total_sessions
            exercises_per_session[month_name] = month_inst.ex_per_session
            sessions_per_week[month_name] = month_inst.sessions_per_week
            total_exercises[month_name] = month_inst.total_exercises

            if verbose:
                print(f"\tParsed Month Meta Data: {month_name}")
                print(f"\t\tTotal Sessions: {month_inst.total_sessions}")
                print(f"\t\tTotal Exercises: {month_inst.total_exercises}")
                print(f"\t\tExercises per Session: {month_inst.ex_per_session}")
                print(f"\t\tSessions per Week: {month_inst.sessions_per_week}")

            # Store values in a dataframe to pivot in g-sheets
            # Sheet, metric, value
            meta_information = pd.DataFrame(
                {
                    "sheet": [month_name*4],
                    "metric": [
                        "total_sessions", 
                        "total_exercises", 
                        "exercises_per_session",
                        "sessions_per_week"
                    ],
                    "value": [
                        month_inst.total_sessions,
                        month_inst.total_exercises,
                        month_inst.ex_per_session,
                        month_inst.sessions_per_week
                    ]
                }
            )

        sessions_per_month = np.mean([int(v) for v in total_sessions.values() if v!=0])
        if verbose:
            print(f"\tAverage Sessions per Month: {sessions_per_month} \n")
            print(meta_information)