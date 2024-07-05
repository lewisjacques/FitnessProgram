from program import Program
import argparse

# Currently updating sheets
known_programs = ('lew', 'hope', 'test',)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Fitness Program Functionality',
        description='Update the program with the latest comments'
    )
    parser.add_argument(
        '--program', default='lew',
        help='Program-name to specify which sheet/legacy comments to access'
    )
    parser.add_argument(
        '--reparse_legacy', action=argparse.BooleanOptionalAction,
        help="reparse a new copy of the legacy Google Sheet comments"
    )
    parser.add_argument(
        '--verbose', action=argparse.BooleanOptionalAction,
        help="Print out additional meta information about the program"
    )
    parser.add_argument(
        '--duplicate', action=argparse.BooleanOptionalAction,
        help="Duplicate program before running any updates"
    )

    args = parser.parse_args()

    assert args.program in known_programs or args.program == "all", \
        f'Program name should be one of {known_programs}'

    ### --- Make Updates to the Program Sheet --- ###
    
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
    #!      - Remove unnecessary pre and post days
    #   - Handle program meta data:
    #       - Get values for sessions, exercises etc
    #!      - Write to home sheet
    #!  - Tidy all days prior to 'today'
    #!      - Merge cells without exercises in them
    #!      - Add titles to days

    if args.program == "all":
        for p in known_programs:
            prog = Program(
                program_name=p,
                reparse_legacy=args.reparse_legacy,
                verbose=args.verbose
            )
    else:
        prog = Program(
            program_name=args.program,
            reparse_legacy=args.reparse_legacy,
            verbose=args.verbose,
            duplicate=args.duplicate
        )