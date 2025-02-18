from flask import Flask, request, jsonify
import json
import requests

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

# Flask App for problem solver
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db

# Konfiguration
HUB_URL = 'http://localhost:5555'
HUB_AUTHKEY = '1234567890'
CHANNEL_AUTHKEY = '1122334455' 
CHANNEL_NAME = "Problem Solver Channel"
CHANNEL_ENDPOINT = "http://localhost:5002"  
CHANNEL_FILE = 'messages.json'
CHANNEL_TYPE_OF_SERVICE = 'aiweb24:problemsolver'
MAX_MESSAGES = 4  #limit number of messages

### von hier ist filter von bad words ----------------------
with open("badwords.txt", "r") as f:
    FILTERED_WORDS = set(word.strip().lower() for word in f.readlines())
      
def censor_message(content):       # censor word with asteriks (*)
    words = content.split()
    censored_words = ["*" * len(word) if word.lower() in FILTERED_WORDS else word for word in words]
    return " ".join(censored_words)

### bis hier ------------------------------------------------

#response options for the problem solver 
PROBLEM_SOLVER_RESPONSE = [
    "Try breaking down your problem into smaller steps.",
    "Have you considered asking someone with experience in this area?",
    "Maybe looking at it from a different perspective can help."
    "Sometimes, stepping away for a moment can help you see the solution more clearly."
    "What’s the real root of the problem? Identifying it can make solving it easier."
    "There’s no single right answer—experiment with different solutions!"
    "Write down all possible solutions, even the crazy ones—you might find a hidden gem."
    "Imagine the problem is already solved—what steps got you there?"
    "What if you reversed the problem? Would that change your approach?"
    "Instead of focusing on what’s wrong, focus on what you can change."
    "Failure isn’t the opposite of success; it’s part of the process."
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
        print("Error creating channel: " + str(response.status_code))
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
    return jsonify({'name': CHANNEL_NAME}), 200

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
    messages.append({
        'content': message['content'],
        'sender': message['sender'],
        'timestamp': message['timestamp'],
        'extra': extra,
    })
    save_messages(messages)

    #sends a problem solver message if it is requested
    if "motivation" in message['content'].lower():
        response_message = random.choice(PROBLEM_SOLVER_RESPONSE)
        channel_response = {
            'content': response_message,
            'sender': 'Problem Solverchannel',
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
    global CHANNEL_FILE, MAX_MESSAGES
     # Limit messages
    if len(messages) > MAX_MESSAGES:
        messages = messages[-MAX_MESSAGES:]  # Save only last one
     
    # Save limited messages
    with open(CHANNEL_FILE, 'w') as f:
        json.dump(messages, f)

if __name__ == '__main__':
    app.run(port=5002, debug=True)
