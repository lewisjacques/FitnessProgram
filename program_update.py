from program import Program
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Fitness Program Functionality',
        description="Update the program with the latest comments"+\
            "Takes a raw copied and pasted comment file from the Google"+\
            "Sheets UI and adds the data into a sheet to keep track of"+\
            "logged comments. \n\nFuture functionality will allow the"+\
            "comments to be extracted through the API directly, this"+\
            "isn't currently possible"
    )
    parser.add_argument(
        '--raw_comments',
        help='Raw text file taken from the Google Sheets UI'
    )
    #! Currently an unavailable option through the Google Sheets API
    parser.add_argument(
        '--extract_api_comments', default=False, action=argparse.BooleanOptionalAction,
        help='If True, access the available comments through the API too'
    )
    # If specified, write parsed comments to local to file-path
    parser.add_argument(
        '--write_to_file', default=False, action=argparse.BooleanOptionalAction,
        help='Flag whether to write parsed comments to local'
    )

    args = parser.parse_args()
    assert isinstance(args.extract_api_comments, bool)

    ### --- Make Updates to the Program Sheet --- ###
    prog = Program(
        comment_file_path=args.raw_comments,
        api_extract=args.extract_api_comments,
        write_to_sheet=True,
        write_to_file=args.write_to_file
    )