import re

class Comment:
    def __init__(self, sheet:str, cell:str, ex:str, dt:str, txt:str):
        self.sheet = sheet
        self.cell = cell
        self.exercise = ex
        self.datetime = dt
        self.comment = txt

    def print_comment(self):
        print(f"""
    Sheet: {self.sheet}
    Cell: {self.cell}
    Exercise: {self.exercise}
    Time-Stamp: {self.datetime}
    Comment: {self.comment}
        """)

class RawCommentFile:
    USERS = "|".join(("Lewis W","Lewis Waite"))
    MONTHS = "|".join(("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"))
    # Eventually move into a sheets request
    SHEETS = "|".join(("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Exercises"))
    RAW_REGEX = (
        fr'(({USERS})\n({SHEETS})\n,\n([A-Z]{{1,2}}'
        fr'[0-9]{{1,3}})\n\|\n([A-Za-z0-9 .,:-;()-]*)'
        fr'\n+({USERS}))?\n({USERS})\n([0-9]{{1,2}}'
        fr'\:[0-9]{{1,2}} [AMPM]{{2}} ({MONTHS}) '
        fr'[0-9]{{1,2}})\n*([A-Za-z0-9 !?,.:-;\'()-]*)'
    )

    def __init__(self, comment:str):
        self.comment = comment
        # Comment store
        self.parsed_comments = self.parse_comment()
    
    def parse_comment(self):
        parsed_comments = []
        self.extracted_input = re.findall(
            self.RAW_REGEX, 
            self.comment
        )
        self.cleaned_input = [
            (p[2], p[3], p[4], 
            p[7].replace('\u202f',''),
            p[9]) for p in self.extracted_input
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
                parsed_comments.append(Comment(
                    sheet=c_sheet, 
                    cell=c_cell, 
                    ex=c_exercise, 
                    dt=c_date, 
                    txt=c_txt
                ))
            except KeyError:
                print("Issue with regex string")
        
        return(parsed_comments)