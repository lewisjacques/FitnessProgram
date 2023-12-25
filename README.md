# FitnessProgram
Code with the intention of building out functionality to improve the usability and efficiency of my Google Sheets training program using Google's APIs

Fitness Program: [Link to Example](https://docs.google.com/spreadsheets/d/1zIt0zCCN63AG1taKVXJ-MxmyQ0c0pjHl1Xhr7x5IDes) ('Anyone with the link' access)

Message me on [LinkedIn](https://www.linkedin.com/in/lewiswaite/) for the *credentials.json* file to create the token to run the program

## program_update.py

The run-file takes one primary argument, **program_name**. This tells program.py which sheet to look at, along with which legacy files.
It also takes a secondary argument **reparse_legacy**, if given, the code will reparse the file found in data/legacy_sheets_comments_<p_name>.csv

An instance of **Program** will be generated with these parameters which will perform the bulk of the heavy lifting

## program.py

#### Reason for two parsing methods in **program.py**

*Comments cannot be read by the Google API as it stands. Notes can be read, but comments are missed out of the meta-data returned by the Sheets API request. This is an issue as all program data Feb-October ('lew') is in the cell comments. A new format has been given to all months thereafter, now, any worksheet with the year appended to the end, 'Dec 23' for example, will be parsed*

### Program
The Program class exists to 
1. Run access authentication
2. Get/Parse archived comments if they exist
3. Parse new format months by generating Session objects stored in a Month object for each sheet
4. Concatenate all workout information
5. Enrich comments by estimating session information given in the exercise notes
6. Write the combined logs to 'Logs via Python'

## sheet.py

### Sheet
Handles the verification process and creates Month objects for each relevant worksheet

## comment.py

### Comment
A class that stores high level raw comment information parsed by RawComment
### RawCommentFile
A class that handles raw test output taken from the Google Sheets UI

## session.py

### Session
Object to store all information relating to the individual gym session

Features include  
- Empty / Rest / Ill / Valid Session Flag
- Total Exercises
- Muscle Groups

## month.py

### Month
Object to store all information relating to the current Month

Features Include
- Session Length
- Month Sessions
- Exercises per Session
- Sessions Per Week