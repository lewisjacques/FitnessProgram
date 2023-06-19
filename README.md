# FitnessProgram
Code with the intention of building out functionality to improve the usability and efficiency of my Google Sheets training program using Google's APIs

*--run_api_port* allows you to run the overall program update along with API functionality to allow requests to be handled through the browser

Running without Google Comments API Extraction  
>  **"python3 program_update.py --raw_comments="data/comments_230511.txt"** --run_api_port=5555

Runninng with the Google Comments API (Currently Unavailable)
> **"python3 program_api.py** --extract_api_comments --run_api_port=5555

## comment.py
### RawCommentFile
A class that handles raw test output taken from the Google Sheets UI

### APIComment
A class that handles extracting comments from the sheet using REST API calls to the Google Sheets API

#### Current problem

*Comments cannot be read by the Google API as it stands. Notes can be read, but comments are missed out of the meta-data returned by the Sheets API request. This is an issue as all program data Feb-June is in the cell comments.*