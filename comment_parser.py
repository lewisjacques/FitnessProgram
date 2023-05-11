import re

class CommentParser:
    USERS = "|".join(("Lewis W","Lewis Waite"))
    MONTHS = "|".join(("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"))
    MULTI_COMMENT = fr'(\n({MONTHS})\n,\n([A-Z]{1,2}[0-9]{1,3})\n\|\n([A-Za-z0-9 ,:-;()-]*)\n({USERS}))?'
    RAW_REGEX = (
        fr'({USERS})\n([0-9]{{1,2}}\:[0-9]{{1,2}} [AMPM]{{2}} '
        fr'({MONTHS}) [0-9]{{1,2}})\n*([A-Za-z0-9 !?,.:-;\'()-]*)' # Months here is actually sheets
        fr'\n({USERS})'
    ) + MULTI_COMMENT*10 # Allow for 10 comments per cell

    def __init__(self, comment:str, type="api"):
        assert type in ("api", "raw"), \
            "Comment type should be \'raw\' or \'api\'"
        self.comment = comment

        if type == "api":
            self.comment_dict = self.parse_api_comment()
        else:
            self.comment_dict = self.parse_raw_comment()
    
    def parse_api_comment(self):
        return
    
    def parse_raw_comment(self):
        self.extracted_input = re.findall(
            self.RAW_REGEX, 
            self.comment
        )
        self.cleaned_input = [
            (p[1].replace("\u202f", " "), 
            p[3], 
            p[6], 
            p[7]
            ) for p in self.extracted_input
        ]

        return