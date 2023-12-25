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
        # Meta information
        self.log_empty_session()
        self.log_rest_session()
        self.log_ill_session()
        self.is_valid = not (self.is_none or self.is_rest or self.is_ill)

        # If day has been recorded as something (including rest and ill)
        if not self.is_none:
            self.title = self.session_data["Session Title"]
            day = re.findall(r"(\d{1,2})", self.title)[0]
            # 0 padding day
            if len(day) == 1:
                day = f"0{day}"
            self.date = f"{month}-{day}"

            # Exercise information
            self.empty_ex = self.check_empty_exercises()
            self.total_ex = session_length - self.empty_ex
            self.incomplete_ex = self.check_incomplete_exercises()
            self.exercises = self.log_exercises()
            self.muscle_groups = self.get_muscle_groups(self.title)

    def print_session_info(self):
        print(f"""\n
            Session Title :: {self.title}\n
            \tTotal Exercises :: {self.total_ex}
            \tEmpty Exercises :: {self.empty_ex}
            \tIncomplete Exercises :: {self.incomplete_ex}
        """)
    
    def log_empty_session(self):
        if all([k.strip()=="" for i,k in enumerate(self.session_data.keys()) if i != 0]):
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
    
    def get_muscle_groups(self, session_title:str):
        return([mg for mg in self.MUSCLE_GROUPS if mg in session_title.upper()])

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