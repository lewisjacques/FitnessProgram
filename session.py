import datetime
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
            month (str): Formatted Month given at the top of the month sheet
        """

        self.session_data = self.check_session_data()
        if self.session_data is None:
            return
        
        self.status = self.log_session_status()
        
        # Meta information
        self.empty_exercise_range = session_data["meta"]["empty_exercise_range"]
        self.session_anchor = session_data["meta"]["session_anchor"]
        self.session_length = session_length
        self.date = session_data["meta"]["date"]
        self.title = self.session_data["Session Title"]

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
        self.date_str = f"{month}-{day}"
        self.day = day

        #! self.muscle_groups = self.get_muscle_groups(self.title)
        #! self.summarise_session()

    def check_session_data(self, session_data:dict):
        # If no session found, set default variables
        if self.session_data is None:
            self.status
            return(None)
        else:
            return(session_data)

    def print_session_info(self):
        print(f"""\n
            Session Title :: {self.title}\n
            \tSession Anchor :: {self.session_anchor}
            \tTotal Exercises :: {self.total_ex}
            \tEmpty Exercises :: {self.empty_ex}
            \tIncomplete Exercises :: {self.incomplete_ex}
        """)

    def log_session_status(self):
        # If arbitrary status added, append them here
        non_primary_statuses = ()
        status = {
            "is_none": False,
            "is_rest": False,
            "is_ill": False,
            "is_holiday": False,
            "is_injured": False,
            "is_valid": False
        }

        # Capture empty session
        if all([k.strip()=="" for i,k in enumerate(self.session_data.keys()) \
            if (i != 0) and (k != "meta")]):
            
            status["is_empty"] = True
        # Capture rest sessions
        if "rest" in [k.lower() for k in self.session_data.keys()]:
            status["is_rest"] = True

        # Capture ill sessions
        if "ill" in [k.lower() for k in self.session_data.keys()]:
            status["is_ill"] = True

        # Capture holiday sessions
        if "holiday" in [k.lower() for k in self.session_data.keys()]:
            status["is_holiday"] = True

        # Capture injured sessions
        if "injured" in [k.lower() for k in self.session_data.keys()]:
            status["is_injured"] = True

        # Extract session validity
        if not(
            status["is_rest"] or \
            status["is_ill"] or \
            status["is_holiday"] or \
            status["is_injured"]
        ):
            status["is_valid"] = True

        ps = {s:v for s,v in status.items() if s not in non_primary_statuses}
        # Check only one primary status is true, else raise a warning
        try:
            assert sum([v for k,v in status.items() \
                if v and k in ps
            ]) == 1, f"""A session should have exactly one primary status. 
            {self.date}\n\t\t{ps}\n\nSession Values: {self.session_data}
            """
        except TypeError:
            raise TypeError(f"""Type error for session:
            {self.date}\n\t\t{ps}\n\nStatus: {status}
            """)

        return(status)

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
            sum([1 for e,r in self.session_data.items() \
                if (e != "") and (r == "")])
        )

    #! Function to write
    def get_muscle_groups(self):
        #
        #  Get exercise sheet

        # Join exercises logged to exercises sheet to get muscle groups

        return
    
    #! Function to write
    def summarise_session(self):
        return
