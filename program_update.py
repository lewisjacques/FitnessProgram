from program import Program
import argparse

known_programs = ('lew', 'hope',)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Fitness Program Functionality',
        description='Update the program with the latest comments'
    )
    # If specified, write parsed comments to local to file-path
    parser.add_argument(
        '--program_name', default='lew',
        help='Program to specify which comments to access'
    )
    parser.add_argument(
        '--reparse_legacy', action=argparse.BooleanOptionalAction,
        help="reparse a new copy of the legacy Google Sheet comments"
    )

    args = parser.parse_args()
    assert args.program_name in known_programs, \
        f'Program name should be one of {known_programs}'

    ### --- Make Updates to the Program Sheet --- ###
    
    prog = Program(
        program_name=args.program_name,
        reparse_legacy=args.reparse_legacy
    )