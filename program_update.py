from program import Program
import argparse

from flask import Flask, request, redirect, url_for, render_template, session

# Flask instance to wrap the functions
app = Flask(__name__)
# Set a secret key to access sessions
app.secret_key = "ProgramAPISecretKey2023"

# Wrapper to let the program know this will be triggered upon load of '/' page
# With a 'GET' method to return some values
@app.route('/', methods=['GET', 'POST'])
def home():
    # If running as an API don't bother with refreshing the sheet 
    prog = Program(
        comment_file_path=None,
        api_extract=False,
        write_to_sheet=False,
        write_to_file=False
    )
    # Split out each exercise DataFrame so the session can load the data
    comment_df = prog.comment_df
    for ex in comment_df['Cell Data'].unique():
        print(f"Adding {ex} to session")
        session[ex] = prog.get_ex_comments(ex).to_json()
        session.modified = True
        
    # If POST request is made redirect to the page with the data
    if request.method == 'POST':
        exercise = request.form['exercise']
        return redirect(url_for('exercise_meta_data', exercise=exercise))
    else:
        rendered = render_template('login.html')
        return rendered

# Wrapper to let the program know this will be triggered upon load of '/exercise' page
# With a 'GET' method to return some values
@app.route('/exercise/<exercise>', methods=['GET'])
def exercise_meta_data(exercise):
    print(f"Getting {exercise} from session")
    json_comments = session.pop(exercise, None)
    if json_comments:
        return(json_comments)
    else:
        return(f"Error, comment_df not found in session.\nSelect one of {list(session.keys())}")

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
    # Port number to run the API through
    parser.add_argument(
        '--run_api_port', default=False,
        help='The port number to run the API through'
    )
    # If specified, write parsed comments to local to file-path
    parser.add_argument(
        '--write_to_file', default=False, action=argparse.BooleanOptionalAction,
        help='Flag whether to write parsed comments to local'
    )

    args = parser.parse_args()
    assert isinstance(args.extract_api_comments, bool)

    if args.run_api_port is not False:
        try:
            port_num = int(args.run_api_port)
            app.run(port=port_num, debug=True)
        except ValueError:
            print("--run_api_port must be an integer")
    else:
        ### --- Make Updates to the Program Sheet --- ###
        prog = Program(
            comment_file_path=args.raw_comments,
            api_extract=args.extract_api_comments,
            write_to_sheet=True,
            write_to_file=args.write_to_file
        )