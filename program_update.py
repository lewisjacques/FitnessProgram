from program import Program
import argparse

known_programs = ('lew', 'hope', 'test')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Fitness Program Functionality',
        description='Update the program with the latest comments'
    )
    # If specified, write parsed comments to local to file-path
    parser.add_argument(
        '--program', default='lew',
        help='Program to specify which comments to access'
    )
    parser.add_argument(
        '--reparse_legacy', action=argparse.BooleanOptionalAction,
        help="reparse a new copy of the legacy Google Sheet comments"
    )
    parser.add_argument(
        '--verbose', action=argparse.BooleanOptionalAction,
        help="Print out additional meta information about the program"
    )

    args = parser.parse_args()
    assert args.program in known_programs or args.program == "all", \
        f'Program name should be one of {known_programs}'

    ### --- Make Updates to the Program Sheet --- ###
    
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
            verbose=args.verbose
        )