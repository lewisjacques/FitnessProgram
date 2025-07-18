from program import Program
import argparse

# Currently updating sheets
known_programs = ('test',)

def main():

    ### --- Make Updates to the Program Sheet --- ###

    # Short Term:
        # - Finish clean_new_month run from add_new_month in sheet.py
        # - Write clean_sessions run from program.py
    
    # Initialise an instance of Program which;

    #   - Read accessable program information from ./program_specs.json
    #   - Input program information initialising a Sheet instance:
    #       - Verifies the user credentials, credentials/sa_program_update.json
    #            via oauth2client
    #       - If testing a duplicate of the program will be created
    #       - Open the sheet with gspread (own API queries on backlog)
    #   - Retrieve (and parse if required) archived comments if they exist
    #   - Get list of all months with format "MMM YY" via Sheet instance
    #   - Concatenate legacy comments with extracted comments
    #   - 'Enrich' logs:
    #       - Extracts weight/time in given comment
    #       - Classifies the exercise with a status (peak, working, static)
    #   - Write logs to sheet "Logs (via Python)", these are processed in the sheet
    #   - Count number of sessions in each month, if there's no empty month
    #       append an additional month:
    #       - Duplicate the "TEMPLATE" sheet with the closest-future month
    #           that doesn't yet exist
    #       - Clean the sheet via Sheet instance
    #!          - Remove unnecessary pre and post days
    #!  - Tidy all days prior to 'today'
    #!      - Merge cells without exercises in them
    #!      - Add titles to days
    #   - Handle program meta data:
    #       - Get values for sessions, exercises etc
    #!      - Write to home sheet
    #!  - Store Template sheets in a seperate document with specified colours 
    #!      and session numbers

    for p in known_programs:
        prog = Program(
            program_name=p,
            reparse_legacy=False,
            verbose=True,
            sheet_names=["all"]
        )
    return(prog)

main()