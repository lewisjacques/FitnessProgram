from program import Program
from time import time
import argparse
import json

from flask import Flask, request

# Flask instance to wrap the functions
app = Flask(__name__)
global data_set

# Wrapper to let the program know this will be triggered upon load of '/' page
# With a 'GET' method to return some values
@app.route('/', methods=['GET'])
def home():
    # Load the dictionary into a JSON object
    json_dump = json.dumps(data_set)

    return(json_dump)

# Wrapper to let the program know this will be triggered upon load of '/' page
# With a 'GET' method to return some values
@app.route('/user/', methods=['GET'])
def user_example():
    user_query = str(request.args.get('user')) # /user/?user=USER_NAME

    data_set = {
        'Page': 'Home',
        'Message': f'User query: {user_query}',
        'Timestamp': time()
    }
    # Load the dictionary into a JSON object
    json_dump = json.dumps(data_set)

    return(json_dump)

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
        help='Raw text file taken from the Google Sheets UI'
    )
    #! Currently an unavailable option through the Google Sheets API
    parser.add_argument(
        '--extract_api_comments', default=False, action=argparse.BooleanOptionalAction,
        help='If True, access the available comments through the API too'
    )
    # Port number to run the API off of
    parser.add_argument(
        '--run_api_port', default="None",
        help='The port number to run the API off of'
    )

    args = parser.parse_args()
    assert isinstance(args.extract_api_comments, bool)

    prog = Program(
        comment_file_path=args.raw_comments,
        api_extract=args.extract_api_comments
    )
    # Update the data being sent to '/'
    data_set = prog.find_working_weight(
        exercise="Dips"
    )

    if args.run_api_port!="None":
        try:
            port_num = int(args.run_api_port)
            app.run(port=port_num, debug=True)
        except ValueError:
            print("If not None, --run_api_port must be an integer")
        except KeyboardInterrupt:
            print("\nEnded\n")
            exit()