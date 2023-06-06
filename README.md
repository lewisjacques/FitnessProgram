# FitnessProgram
Building out functionality to improve the usability and efficiency of my Google Sheets training program using Google's APIs  
> Run with *"python3 update_program.py --raw_comments="data/comments_230511.txt"*

### RawCommentFile
A class that handles raw test output within the Google Sheets UI

### APIComment
A class that handles extracting comments from the sheet using REST API calls to the Google Sheets API

## Current problem

Comments cannot be read by the Google API as it stands. Notes can be read but comments are missed out of the meta-data. This is an issue as all program data Feb-June is in the cell comments. From here onwards this will be stored as a note, notes can be retrieved through the API