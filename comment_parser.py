import re

class CommentParser:
    # RAW_REGEX = r"({{users}})\n([0-9]{{1,2}}:[0-9]{{1,2}} [AMPM]{{2}} ({{months}}) [0-9]{{1,2}})\n*([A-Za-z0-9 !?,.:-;'()-]*)\n({{users}})\n({{months}})\n,\n([A-Z]{{1,2}}[0-9]{{1,3}})\n\|\n([A-Za-z0-9 ,:-;()-]*)"
    RAW_REGEX = r"(Lewis W|Lewis Waite)\n([0-9]{1,2}:[0-9]{1,2} [AMPM]{2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) [0-9]{1,2})\n*([A-Za-z0-9 !?,.:-;'()-]*)\n(Lewis W|Lewis Waite)\n(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\n,\n([A-Z]{1,2}[0-9]{1,3})\n\|\n([A-Za-z0-9 ,:-;()-]*)"
    USERS = ("Lewis W","Lewis Waite")

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
        users = ("Lewis W","Lewis Waite")
        months = ("Jan","Feb","Mar","Apr",
                  "May","Jun","Jul","Aug",
                  "Sep","Oct","Nov","Dec")
        
        regex = self.RAW_REGEX.format(
            users="|".join(users),
            months="|".join(months)
        )
        self.extracted_input = re.findall(regex, self.comment)
        self.cleaned_input = [(p[1], p[3], p[6], p[7]) for p in self.extracted_input]

        return