# FitnessProgram
Building out functionality to improve the usability and efficiency of my Google Sheets training program using Google's APIs

## Current problem

Comments cannot be read by the Google API, this is an issue as all program data Feb-May is in the cell comments. From here onwards this will be stored as a note, notes can be retrieved through the API


So two functions need developing.
- Web-comment parser (copied and pasted raw text)
- API CellData Object parser


Both of these will be written into the CommentParser class with arguments to differentiate the source type