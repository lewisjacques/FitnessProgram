import re
import pandas as pd

class Comment:
    def __init__(self, sheet:str, cell:str, ex:str, dt:str, txt:str):
        self.sheet = sheet
        self.cell = cell
        self.exercise = ex
        self.datetime = dt
        self.comment = txt

    def print_comment(self):
        print(
            f"\tSheet: {self.sheet}\n",
            f"\tCell: {self.cell}\n",
            f"\tCell Data: {self.exercise}\n",
            f"\tTime-Stamp: {self.datetime}\n",
            f"\tComment: {self.comment}"
        )

class RawCommentFile:
    USERS = "|".join(("Lewis W","Lewis Waite","hope phillips-hemming"))
    MONTHS = "|".join(("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"))
    # Eventually move into a sheets request
    SHEETS = "|".join(("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Exercises"))
    RAW_REGEX = (
        fr'(({USERS})\n({SHEETS})\n,\n([A-Z]{{1,2}}'
        fr'[0-9]{{1,3}})\n\|\n([A-Za-z0-9 &.,:-;()-/]*)'
        fr'\n+({USERS}))?\n({USERS})\n(([0-9]{{1,2}}'
        fr'\:[0-9]{{1,2}} [AMPM]{{2}} ({MONTHS}) '
        fr'[0-9]{{1,2}})|(({MONTHS}) [0-9]{{1,2}}, [0-9]{{4}}))\n*([A-Za-z0-9 !?,.:-;\'()-/]*)'
    )
    # May 30, 2023
    # 10:39 AM May 2023

    def __init__(self, raw_comments:str):
        parsed_comment_list = self.parse_comment(raw_comments)
        self.parsed_comment_df = self.build_comment_df(parsed_comment_list)
    
    def parse_comment(self, raw_comments:str):
        parsed_comments = []
        self.extracted_input = re.findall(
            self.RAW_REGEX, 
            raw_comments
        )

        self.cleaned_input = [
            (p[2], p[3], p[4], 
            p[7].replace('\u202f',''),
            p[12]) for p in self.extracted_input
        ]

        # Only the top comment has the meta data
        # Store the rolling meta-data variables
        r_sheet=None
        r_cell=None
        r_exercise=None
        for com in self.cleaned_input:
            try:
                # Set the current variables
                c_sheet=com[0]
                c_cell=com[1]
                c_exercise=com[2]
                # If the above values are empty in this comment
                if all([
                    c_sheet=='',
                    c_cell=='',
                    c_exercise==''
                ]):
                    # If rolling variables haven't been set yet
                    if all([
                        r_sheet==None,
                        r_cell==None,
                        r_exercise==None
                    ]):
                        # The comment file hasn't reached its first value
                        continue

                    # Then take the values from the latest found
                    c_sheet=r_sheet
                    c_cell=r_cell
                    c_exercise=r_exercise               
                else:
                    # Reset the rolling variables
                    r_sheet=c_sheet
                    r_cell=c_cell
                    r_exercise=c_exercise

                c_date = com[3]
                c_txt = com[4]

                comment = Comment(
                    sheet=c_sheet, 
                    cell=c_cell, 
                    ex=c_exercise, 
                    dt=c_date, 
                    txt=c_txt
                )
                parsed_comments.append(comment)
            except KeyError:
                print("Issue with regex string")
        
        return(parsed_comments)

    def build_comment_df(self, parsed_comments:list):
        """
        Build comment data frame for archived comments
        that have been parsed using comment.py

        Args:

        """
        default_comments = [
            "Marked as resolved",
            "Re-opened"
        ]
        # Convert parsed comments into a dataframe
        comment_df = pd.DataFrame(
            columns=[
                "Sheet",
                "Cell",
                "Cell Data",
                "Time-Stamp",
                "Comment"
            ]
        )
        for com in parsed_comments:
            title_cell = re.search("(\d{1,2})", com.exercise)
            if com.comment not in default_comments and title_cell is None:
                comment_df = pd.concat(
                    [
                        pd.DataFrame({
                            "Sheet": com.sheet,
                            "Cell": com.cell,
                            "Cell Data": com.exercise,
                            "Time-Stamp": com.datetime,
                            "Comment": com.comment
                        }, index=[0]),
                        comment_df
                    ],
                    ignore_index=True
                )

        # Add date to dataframe
        # Split dataframe into rows with AM/PM and the other date format
        comment_df_ampm = comment_df.loc[comment_df["Time-Stamp"].str.contains(":")].copy()
        comment_df_ampm["Date"] = pd.to_datetime(comment_df_ampm["Time-Stamp"], format="%I:%M%p %b %d")
        comment_df_ampm["Date"] = comment_df_ampm["Date"].map(lambda x : x.replace(year=2023).strftime('%Y-%m-%d'))

        comment_df_year_stamp = comment_df.loc[~comment_df["Time-Stamp"].str.contains(":")].copy()
        comment_df_year_stamp["Date"] = pd.to_datetime(comment_df_year_stamp["Time-Stamp"], format="%b %d, %Y")
        comment_df_year_stamp["Date"] = comment_df_year_stamp["Date"].map(lambda x : x.strftime('%Y-%m-%d'))

        # Concatenate the dataframes with correct date formats
        comment_df = pd.concat((comment_df_ampm, comment_df_year_stamp))
        # Sort by Month and date
        comment_df.sort_values(by=["Sheet", "Date"], axis=0, inplace=True)

        return(comment_df)
    
    def save_to_local(self, parsed_comment_location:str):
        # Write to Local File 
        self.parsed_comment_df.to_csv(parsed_comment_location, index=False)