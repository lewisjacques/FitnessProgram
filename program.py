from comment import RawCommentFile

from dateutil.relativedelta import relativedelta
from datetime import datetime
from sheet import Sheet
import pandas as pd
import numpy as np
import yaml
import os
import re

class Program:
    PROGRAM_SPECS_PATH = "program_specs.yaml"

    def __init__(
            self, 
            program_name:str, 
            reparse_legacy:bool, 
            verbose:bool,
            sheet_names:list[str],
            duplicate:bool=False
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

        with open(self.PROGRAM_SPECS_PATH, 'r') as file:
            self.program_specs = yaml.safe_load(file)

        print(f"\n### --- Parsing Program: {self.program_specs[program_name]['pretty']} --- ###")

        # Pull out variables for the relevant sheet
        program_specs = self.program_specs[program_name]
        parsed_comment_location = program_specs['parsed_comments']
        legacy_comment_location = program_specs['legacy_comments']
        spreadsheet_id = program_specs['sheet_id']

        # If running the testing program, duplicate by default
        if program_name == "test":
            duplicate = True

        ### --- Create Sheet Instance --- ###

        # Initialise sheet access, duplicate sheet if duplicate=True and parse months
        self.sheet = Sheet(
            program_name, 
            spreadsheet_id, 
            duplicate, 
            verbose,
            sheet_names,
            clean_parsed_months=True
        )

        ### --- Get / Generate Archived Comments --- ###

        # Returns None if no data provided
        # legacy_exercise_df = self.get_archived_comments(
        #     parsed_comment_location,
        #     legacy_comment_location,
        #     reparse_legacy
        # )

        # # ### --- Combine Legacy and New Format Month Data --- ###

        # all_exercise_df = self.concatenate_all_months(
        #     legacy_exercise_df,
        #     self.sheet.month_instances
        # )

        # # ### --- Enrich Logged Results --- ###

        # enriched_logs_df = self.enrich_logs(all_exercise_df)

        # # Write newly parsed comments to the sheet
        # self.sheet.write_to_sheet(
        #     df=enriched_logs_df,
        #     tab_name="Logs (via Python)"
        # )

        ### --- Add Missing Months --- ###

        # all_months = [m.sheet_name for m in self.sheet.month_instances.values()]

        # current_month_dt = datetime.now()
        # current_month_str = current_month_dt.strftime("%b %y")
        # next_month_dt = datetime.now() + relativedelta(months=1)
        # next_month_str = next_month_dt.strftime("%b %y")

        # # Always be one month ahead
        # if current_month_str not in all_months:
        #     # Add new month (if necessary) and clean the formatting with clean_new_month()
        #     self.sheet.add_new_month(current_month_dt, clean=clean_month)
        # if next_month_str not in  all_months:
        #     # Add new month (if necessary) and clean the formatting with clean_new_month()
        #     self.sheet.add_new_month(next_month_dt, clean=True)

        ### --- Program Meta --- ###

        #! self.get_program_meta(self.sheet.month_instances, verbose)

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
        month_instances:dict
    ):
        """
        Concatenate legacy comments with new format months

        Args:
            exercise_df (pd.DataFrame): Legacy exercise data-frame
            month_instances (dict): month_sheet_name:str, month_instance:Month
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
        for month_instance in month_instances.values():
            for session in month_instance.month_sessions:
                # Not empty and not a rest day
                if session.status["is_valid"]:
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
        Get a rough estimate of the exercise result. Long term this will be an 
        NLP-like system of finding similar strings

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
    
    # Get program meta data by gathering together the month meta data extracted
    def get_program_meta(self, month_instances:dict, verbose:bool):
        # --- Add Historical Meta Data --- #

        total_sessions = {}
        total_exercises = {}
        exercises_per_session = {}
        sessions_per_week = {}
        
        for month_name, month_inst in month_instances.items():
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