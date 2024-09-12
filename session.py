import re

class Session:
    MUSCLE_GROUPS = [
        "BACK",
        "LEGS",
        "BICEPS",
        "TRICEPS",
        "CHEST",
        "SHOULDERS",
        "CARDIO"
    ]

    def __init__(
        self, 
        session_data:dict, 
        session_length:int,
        month:str
    ):
        """
        Empty Session: No information given in any cell
        Rest session: "REST" is found as a given 'exercise'
        Valid Session: Not an empty session or a rest session

        Args:
            session_data (dict): exercise, result key-value
            session_length (int): Max exercises per session for the month
            month (str): Formatted Month given at the top of the month program
        """
        self.session_data = session_data
        self.empty_exercise_range = session_data["meta"]["empty_exercise_range"]
        self.session_anchor = session_data["meta"]["session_anchor"]
        self.session_length = session_length

        # Meta information
        self.log_empty_session()
        self.log_rest_session()
        self.log_ill_session()
        self.log_injured_session()
        self.log_holiday_session()
        self.is_valid = not(self.is_none or self.is_rest or self.is_ill or self.is_holiday or self.is_injured)

        self.title = self.session_data["Session Title"]

        # If day has been recorded as something (including rest and ill)
        if not self.is_none:
            # Exercise information
            self.empty_ex = self.check_empty_exercises()
            self.total_ex = session_length - self.empty_ex - 1 # -1 for Date row
            self.incomplete_ex = self.check_incomplete_exercises()
            self.exercises = self.log_exercises()

            try:
                day = re.findall(r"(\d{1,2})", self.title)[0]
            except IndexError:
                print(f"Error with title: {self.title}")
                self.print_session_info()
                raise(IndexError)
            # 0 padding day
            if len(day) == 1:
                day = f"0{day}"
            self.date = f"{month}-{day}"

















            # self.muscle_groups = self.get_muscle_groups(self.title)
        else:
            self.date = None
            self.empty_ex = None
            self.total_ex = None
            self.incomplete_ex = None
            self.exercises = None
            self.muscle_groups = None

    def print_session_info(self):
        print(f"""\n
            Session Title :: {self.title}\n
            \tSession Anchor :: {self.session_anchor}
            \tTotal Exercises :: {self.total_ex}
            \tEmpty Exercises :: {self.empty_ex}
            \tIncomplete Exercises :: {self.incomplete_ex}
        """)
    
    def log_empty_session(self):
        if all([
            k.strip()=="" for i,k in enumerate(self.session_data.keys()) \
                if (i != 0) and (k != "meta")
            ]
        ):
            self.is_none = True
        else:
            self.is_none = False

    def log_rest_session(self):
        if "rest" in [k.lower() for k in self.session_data.keys()]:
            self.is_rest = True
        else:
            self.is_rest = False

    def log_ill_session(self):
        if "ill" in [k.lower() for k in self.session_data.keys()]:
            self.is_ill = True
        else:
            self.is_ill = False

    def log_holiday_session(self):
        if "holiday" in [k.lower() for k in self.session_data.keys()]:
            self.is_holiday = True
        else:
            self.is_holiday = False

    def log_injured_session(self):
        if "injured" in [k.lower() for k in self.session_data.keys()]:
            self.is_injured = True
        else:
            self.is_injured = False

    def log_exercises(self):
        exercises = {}
        for ex, res in self.session_data.items():
            # Don't add title or incomplete exercises
            if ex == "Session Title" or res == "":
                continue
            else:
                exercises[ex] = res
        return(exercises)

    def check_empty_exercises(self):
        if "" in self.session_data.keys():
            return(self.session_data[""])
        else:
            return(0)
    
    def check_incomplete_exercises(self):
        return(
            sum(
                [1 for e,r in self.session_data.items() \
                    if (e != "") and (r == "")]
            )
        )
    
    def get_muscle_groups(self):
        # Get exercise sheet

        # Join exercises logged to exercises sheet to get muscle groups












        return

    @property
    def is_none(self) -> bool:
        return(self._is_none)
    
    @is_none.setter
    def is_none(self, non_flag:bool):
        self._is_none = non_flag

    @property
    def is_rest(self) -> bool:
        return(self._is_rest)
    
    @is_rest.setter
    def is_rest(self, rest_flag:bool):
        self._is_rest = rest_flag

    @property
    def is_ill(self) -> bool:
        return(self._is_ill)
    
    @is_ill.setter
    def is_ill(self, rest_flag:bool):
        self._is_ill = rest_flag

    @property
    def is_holiday(self) -> bool:
        return(self._is_holiday)
    
    @is_holiday.setter
    def is_holiday(self, hol_flag:bool):
        self._is_holiday = hol_flag

    @property
    def is_injured(self) -> bool:
        return(self._is_injured)
    
    @is_injured.setter
    def is_injured(self, inj_flags:bool):
        self._is_injured = inj_flags

    def merge_cells(self, g_sheet, sheet_id):
        # If the day contains session data
        if self.is_valid:
            body = {
                "requests": [
                    {
                        "mergeCells": {
                            "mergeType": "MERGE_ALL",
                            "range": {  
                                "sheetId": sheet_id,
                                "startRowIndex": self.empty_exercise_range["start"][0],
                                "endRowIndex": self.empty_exercise_range["end"][0],
                                "startColumnIndex": self.empty_exercise_range["start"][1],
                                "endColumnIndex": self.empty_exercise_range["end"][1]
                            }
                        }
                    }
                ]
            }
        # Otherwise just one cell should contain "REST", "ILL" etc.
        else:
            top_exercise_row = self.session_anchor[0]+1
            bot_exercise_row = self.session_anchor[0]+1 + \
                self.session_length -1
            top_exercise_col = self.session_anchor[1]
            bot_exercise_col = self.session_anchor[1] + 1

            body = {
                "requests": [
                    {
                        "mergeCells": {
                            "mergeType": "MERGE_ALL",
                            "range": {  
                                "sheetId": sheet_id,
                                "startRowIndex": top_exercise_row,
                                "endRowIndex": bot_exercise_row,
                                "startColumnIndex": top_exercise_col,
                                "endColumnIndex": bot_exercise_col
                            }
                        }
                    }
                ]
            }

        print(f"MERGING:\n{body}")

        res = g_sheet.batch_update(body)
        return(res)