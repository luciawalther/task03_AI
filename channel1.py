## channel.py - a simple message channel
##

from flask import Flask, request, render_template, jsonify
import json
import requests
import random

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

# Create Flask app for motivation channel 
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db

HUB_URL = 'http://localhost:5555'
HUB_AUTHKEY = '1234567890'
CHANNEL_AUTHKEY = '0987654321'
CHANNEL_NAME = "Motivation Channel"
CHANNEL_ENDPOINT = "http://localhost:5001" # don't forget to adjust in the bottom of the file
CHANNEL_FILE = 'messages.json'
CHANNEL_TYPE_OF_SERVICE = 'aiweb24:chat'
MAX_MESSAGES = 4  #limit number of messages

### von hier ist filter von bad words ----------------------
with open("badwords.txt", "r") as f:
    FILTERED_WORDS = set(word.strip().lower() for word in f.readlines())
      
def censor_message(content):       # censor word with asteriks (*)
    words = content.split()
    censored_words = ["*" * len(word) if word.lower() in FILTERED_WORDS else word for word in words]
    return " ".join(censored_words)

### bis hier ------------------------------------------------

# Motivate quoats for the response 
MOTIVATION_QUOTES = [
    "Never give up! Every day is a new chance.",
    "You are stronger than you think!",
    "Keep going, even when it gets tough. Success is waiting at the end of the road!",
    "Every journey begins with a single step.",
    "The best is yet to come!",
    "Believe in yourself – you can achieve anything!",
    "Mistakes are just steps on the path to success.",
    "No matter how slow you move forward, you're still ahead of those who do nothing.",
    "Difficult roads often lead to beautiful destinations.",
    "Your only limit is the one you set for yourself.",
    "Every challenge you overcome makes you stronger.",
    "Small progress is still progress.",
    "You don’t have to be perfect to be amazing.",
    "Your potential is endless – go explore it!",
    "You have everything you need to succeed – believe in yourself!",
    "Every day is an opportunity to grow and improve.",
    "Be proud of how far you’ve come, and keep going!",
    "You are capable of more than you know."
   ]



@app.cli.command('register')
def register_command():
    global CHANNEL_AUTHKEY, CHANNEL_NAME, CHANNEL_ENDPOINT

    # send a POST request to server /channels
    response = requests.post(HUB_URL + '/channels', headers={'Authorization': 'authkey ' + HUB_AUTHKEY},
                             data=json.dumps({
                                "name": CHANNEL_NAME,
                                "endpoint": CHANNEL_ENDPOINT,
                                "authkey": CHANNEL_AUTHKEY,
                                "type_of_service": CHANNEL_TYPE_OF_SERVICE,
                             }))

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

    # add message to messages
    messages = read_messages()
    messages.append({'content': content,
                     'sender': message['sender'],
                     'timestamp': message['timestamp'],
                     'extra': extra,
                     })
    save_messages(messages)

    #sends a motivation quoat if its requested 
    if "motivation" in message['content'].lower():
        response_message = random.choice(MOTIVATION_QUOTES)
        channel_response = {
            'content': response_message,
            'sender': 'Movtion channel',
            'timestamp': message['timestamp'],  
            'extra': None,
        }
        messages.append(channel_response)
        save_messages(messages)

    return "OK", 200

def read_messages():
    global CHANNEL_FILE, MAX_MESSAGES
    try:
        with open(CHANNEL_FILE, 'r') as f:
            messages = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        messages = []

  

     # Limit messages
    if len(messages) > MAX_MESSAGES:
        messages = messages[-MAX_MESSAGES:]  # Save only last one


    return messages


def save_messages(messages):
    global CHANNEL_FILE,  MAX_MESSAGES

         # Limit messages
    if len(messages) > MAX_MESSAGES:
        messages = messages[-MAX_MESSAGES:]  # Save only last one
     
    # Save limited messages
    with open(CHANNEL_FILE, 'w') as f:
        json.dump(messages, f)

# Start development web server
# run flask --app channel.py register
# to register channel with hub

if __name__ == '__main__':
    app.run(port=5001, debug=True)
