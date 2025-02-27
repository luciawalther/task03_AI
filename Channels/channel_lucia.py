## channel.py - a simple message channel
##

from flask import Flask, request, render_template, jsonify
import json
import requests
import re


# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db

HUB_URL = 'http://localhost:5555'
HUB_AUTHKEY = '1234567890'
CHANNEL_AUTHKEY = '0987654321'
CHANNEL_NAME = "The One Channel"
CHANNEL_ENDPOINT = "http://localhost:5001" # don't forget to adjust in the bottom of the file
CHANNEL_FILE = 'messages.json'
CHANNEL_TYPE_OF_SERVICE = 'aiweb24:chat'


### von hier ist filter von bad words ----------------------
with open("badwords.txt", "r") as f:
    FILTERED_WORDS = set(word.strip().lower() for word in f.readlines())
      
def censor_message(content):       # censor word with asteriks (*)
    words = content.split()
    censored_words = ["*" * len(word) if word.lower() in FILTERED_WORDS else word for word in words]
    return " ".join(censored_words)

### bis hier ------------------------------------------------


@app.cli.command('register')
def register_command():
    global CHANNEL_AUTHKEY, CHANNEL_NAME, CHANNEL_ENDPOINT

    # send a POST request to server /channels
    response = requests.post(HUB_URL + '/channels', headers={'Authorization': 'authkey ' + HUB_AUTHKEY},
                             json ={ #data=json.dumps({
                                "name": CHANNEL_NAME,
                                "endpoint": CHANNEL_ENDPOINT,
                                "authkey": CHANNEL_AUTHKEY,
                                "type_of_service": CHANNEL_TYPE_OF_SERVICE,
                             })

    if response.status_code != 200:
        print("Error creating channel: "+str(response.status_code))
        print(response.text)
        return

def check_authorization(request):
    global CHANNEL_AUTHKEY
    # check if Authorization header is present
    if 'Authorization' not in request.headers:
        return False
    # check if authorization header is valid
    if request.headers['Authorization'] != 'authkey ' + CHANNEL_AUTHKEY:
        return False
    return True

@app.route('/health', methods=['GET'])
def health_check():
    global CHANNEL_NAME
    if not check_authorization(request):
        return "Invalid authorization", 400
    return jsonify({'name':CHANNEL_NAME}),  200

# GET: Return list of messages
@app.route('/', methods=['GET'])
def home_page():
    if not check_authorization(request):
        return "Invalid authorization", 400
    # fetch channels from server
    return jsonify(read_messages())

# POST: Send a message
@app.route('/', methods=['POST'])
def send_message():
    # fetch channels from server
    # check authorization header
    if not check_authorization(request):
        return "Invalid authorization", 400
    
    # check if message is present
    message = request.json
    if not message:
        return "No message", 400
    if not 'content' in message:
        return "No content", 400
    if not 'sender' in message:
        return "No sender", 400
    if not 'timestamp' in message:
        return "No timestamp", 400
    if not 'extra' in message:
        extra = None
    else:
        extra = message['extra']

    ### Content definiert mit dem Fall dass ein Schimpfwort drin ist! -----------------
    content = censor_message(message['content'])

    # add message to messages (1 ÄNDERUNG!!!)
    messages = read_messages()
    messages.append({'content': content,   # das geändert zu content (oben definiert) damit die richtige Nachricht gespeichert wird
                     'sender': message['sender'],
                     'timestamp': message['timestamp'],
                     'extra': extra,
                    })
    save_messages(messages)
    return "OK", 200


def read_messages():
    global CHANNEL_FILE
    try:          # more safe with open geändert!!!!!!!!!!
        with open(CHANNEL_FILE, 'r') as f:
            return json.load(f)
       
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    
def save_messages(messages):
    global CHANNEL_FILE
    with open(CHANNEL_FILE, 'w') as f:    # more safe with open geändert!!!!!!!!
        json.dump(messages, f)

# Start development web server
# run flask --app channel.py register
# to register channel with hub

if __name__ == '__main__':
    app.run(port=5001, debug=True)
