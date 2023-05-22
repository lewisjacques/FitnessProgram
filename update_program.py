from program import Program
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Fitness Program Functionality',
        description="Update the program with the latest comments"+\
            "Takes a raw copied and pasted comment file from the Google"+\
            "Sheets API and adds the data into a sheet to keep track of"+\
            "logged comments. \n\nFuture functionality will allow the"+\
            "comments to be extracted through the API directly, this"+\
            "isn't currently possible"
    )
    parser.add_argument(
        '--raw_comments',
        help='File copied and pasted from the Google Sheets UI'
    )
    parser.add_argument(
        '--api_comments', default=False,
        help='If True, access the available comments through the API too'
    )

    args = parser.parse_args()
    assert isinstance(args.api_comments, bool)

    prog = Program(
        comment_file_path=args.raw_comments,
        api_extract=args.api_comments
    )