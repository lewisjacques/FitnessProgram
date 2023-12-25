from comment import RawCommentFile
from sheet import Sheet
import pandas as pd
import os
import re

class Program:
    PROGRAM_SPECS = {
        "lew": {
            "legacy_comments": \
                '/Users/ljw/Projects/FitnessProgram/data/legacy_sheets_comments_lew.txt',
            'parsed_comments': \
                "/Users/ljw/Projects/FitnessProgram/data/parsed_comments_lew.csv",
            'sheet_id':'1zIt0zCCN63AG1taKVXJ-MxmyQ0c0pjHl1Xhr7x5IDes'
        },
        "hope": {
            "legacy_comments": \
                '/Users/ljw/Projects/FitnessProgram/data/legacy_sheets_comments_hope.txt',
            'parsed_comments': \
                "/Users/ljw/Projects/FitnessProgram/data/parsed_comments_hope.csv",
            'sheet_id':'1CL_1w43DVqBd86OogLwJEgH5VgzuxIqKKlLDY9B2L44'
        }
    }

    def __init__(self, program_name:str=None, reparse_legacy:bool=False):
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

        # Pull out variables for the relevant sheet
        program_specs = self.PROGRAM_SPECS[program_name]
        parsed_comment_location = program_specs['parsed_comments']
        legacy_comment_location = program_specs['legacy_comments']
        sheet_id = program_specs['sheet_id']
        
        # Initialise sheet access
        sheet = Sheet(sheet_id)

        ### --- Get / Generate Archived Comments --- ###

        legacy_exercise_df = self.get_archived_comments(
            parsed_comment_location,
            legacy_comment_location,
            reparse_legacy
        )

        ### --- Parse New Format Months --- ###

        # Get new format months
        new_format_months = [
            s.title for s in sheet.g_sheet.worksheets() \
                if re.search(" \d{2}", s.title) is not None
        ]
        
        # key: month name, value: Month instance
        month_sessions = sheet.parse_months(new_format_months)

        ### --- Combine Legacy and New Format Month Data --- ###

        all_exercise_df = self.concatenate_all_months(
            legacy_exercise_df,
            month_sessions
        )

        ### --- Enrich Logged Results --- ###

        enriched_logs_df = self.enrich_logs(all_exercise_df)

        # Write newly parsed comments to the sheet
        sheet.write_to_sheet(
            df=enriched_logs_df,
            tab_name="Logs (via Python)"
        )

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

        # If we need to parse the legacy comments into a readable format
        if not os.path.isfile(parsed_comment_location) or reparse_legacy:
            with open(legacy_comment_location) as coms:
                legacy_comments = ''.join(coms.readlines())

            # Parse the raw comments getting rid of unnecessary information with re
            raw_comments = RawCommentFile(legacy_comments)
            raw_comments.save_to_local(parsed_comment_location)
            exercise_df = raw_comments.parsed_comment_df
        else:
            exercise_df = pd.read_csv(parsed_comment_location)
        return(exercise_df)
    
    def concatenate_all_months(
        self,
        exercise_df:pd.DataFrame,
        month_sessions:dict
    ):
        """
        Concatenate legacy comments with new format months

        Args:
            exercise_df (pd.DataFrame): Legacy exercise data-frame
            month_sessions (dict): month_sheet_name:str, month_instance:Month
        """

        exercise_df = exercise_df.loc[:, [
            "Date",
            "Cell Data",
            "Comment"
        ]].copy()
        exercise_df.rename(columns={
            "Cell Data": "Exercise",
            "Comment": "Result"
        }, inplace=True)

        # For each month add every valid exercise to the exercise df
        for month_instance in month_sessions.values():
            for session in month_instance.month_sessions:
                # Not empty and not a rest day
                if session.is_valid:
                    for ex, result in session.exercises.items():
                        # Skipped exercise block
                        if ex == "":
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
        if re.search(r"(working)", str(result).lower()) is not None:
            return("Working")
        if re.search(r"(peak)", str(result).lower()) is not None:
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