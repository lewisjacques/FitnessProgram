# FitnessProgram
Code with the intention of building out functionality to improve the usability and efficiency of my Google Sheets training program using Google's APIs

Fitness Program: [Link to Sheet](https://docs.google.com/spreadsheets/d/1LyZsxwUsc5PSdzQT_2G3HZxty9rWwR-laV48spNrOQI/edit#gid=1341696163) ('Anyone with the link' access)

Message me on [LinkedIn](https://www.linkedin.com/in/lewiswaite/) for the *credentials.json* file to run the program for the first time

## program_update.py

The runtime program with API functionality built into the file using **flask** routing

*--run_api_port* allows you to run the overall program update, along with API functionality to allow requests to be handled through the browser

Running without Google Comments API Extraction  
>  **python3 program_update.py** --raw_comments="data/comments_130623.txt"  --run_api_port=5566

Running with the Google Comments API (Currently Unavailable)
> **"python3 program_api.py** --extract_api_comments --run_api_port=5555

## comment.py
### RawCommentFile
A class that handles raw test output taken from the Google Sheets UI

### APIComment
A class that (will) handle extracting comments from the sheet using REST API calls to the Google Sheets API

#### Current problem

*Comments cannot be read by the Google API as it stands. Notes can be read, but comments are missed out of the meta-data returned by the Sheets API request. This is an issue as all program data Feb-June is in the cell comments.*

## program.py

### Program
The Program class exists to 
- Validate the user running the update
- Based on the arguments passed to the class, build a class variable 'comment_df' either from a raw text file, or through the Google Sheets API
- Write the parsed comments to the sheet
- Write the parsed comments to local