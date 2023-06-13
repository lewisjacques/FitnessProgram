from flask import Flask, request
import json
import time

# Flask instance tow rap the functions
app = Flask(__name__)

# Wrapper to let the program know this will be triggered upon load of '/' page
# With a 'GET' method to return some values
@app.route('/', methods=['GET'])
def home():
    data_set = {
        'Page': 'Home',
        'Message': 'Success',
        'Timestamp': time.time()
    }
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
        'Timestamp': time.time()
    }
    # Load the dictionary into a JSON object
    json_dump = json.dumps(data_set)

    return(json_dump)

if __name__ == "__main__":
    app.run(port=5556)