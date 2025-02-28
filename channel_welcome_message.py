## channel.py - a simple message channel

from flask import Flask, request, render_template, jsonify
import json
import requests
import random
import os

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

# Create Flask app for motivation channel 
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # Load configuration
app.app_context().push()  # Create an app context before initializing db

# Define constants for the hub and channel settings
HUB_URL = 'http://vm146.rz.uni-osnabrueck.de/hub'
HUB_AUTHKEY = 'Crr-K24d-2N'
CHANNEL_AUTHKEY = '0987654321'
CHANNEL_NAME = "Motivation Channel"
CHANNEL_ENDPOINT = "http://vm146.rz.uni-osnabrueck.de/u097/ai_task03/channel.wsgi" #localhost:5001" # Update this URL if necessary
CHANNEL_FILE = 'messages.json'  # File to store messages
CHANNEL_TYPE_OF_SERVICE = 'aiweb24:chat'
MAX_MESSAGES = 20  # Limit the number of stored messages
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BADWORDS_FILE = os.path.join(BASE_DIR, 'badwords.txt')

# Welcome message displayed when the channel is opened
WELCOME_MESSAGE = {
    'content': "Welcome to your motivation channel. You need motivation? Just write 'Motivation needed' and I will help to motivate you. This channel is a platform for mutual exchange and also to increase each other's motivation. So get started and share your situation",
    'sender': 'Motivation Channel',
    'timestamp': 'system',
    'extra': None,
}

# Load filtered words for censoring inappropriate messages
with open(BADWORDS_FILE, "r") as f:
    FILTERED_WORDS = set(word.strip().lower() for word in f.readlines())

# Function to censor inappropriate words
# Replaces banned words with asterisks (*)
def censor_message(content):
    words = content.split()
    censored_words = ["*" * len(word) if word.lower() in FILTERED_WORDS else word for word in words]
    return " ".join(censored_words)

# List of motivation quotes for automatic replies
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

# Register the channel with the hub
@app.cli.command('register')
def register_command():
    global CHANNEL_AUTHKEY, CHANNEL_NAME, CHANNEL_ENDPOINT

    # Send a POST request to the hub to register the channel
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

# Function to check authorization for requests
def check_authorization(request):
    global CHANNEL_AUTHKEY
    # Check if Authorization header is present
    if 'Authorization' not in request.headers:
        return False
    # Validate the authorization key
    if request.headers['Authorization'] != 'authkey ' + CHANNEL_AUTHKEY:
        return False
    return True

# Health check endpoint
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
    messages = read_messages()
    #welcome message is displayed when channel is opened
    response_messages = [WELCOME_MESSAGE] + messages
    
    return jsonify(response_messages)

# POST: Send a message to the channel
@app.route('/', methods=['POST'])
def send_message():
    if not check_authorization(request):
        return "Invalid authorization", 400
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

    # Censor inappropriate words
    content = censor_message(message['content'])
    messages = read_messages()
    messages.append({'content': content,
                     'sender': message['sender'],
                     'timestamp': message['timestamp'],
                     'extra': extra,
                     })
    save_messages(messages)

    # Automatically respond with a motivation quote if requested
    if "motivation" in message['content'].lower():
        response_message = random.choice(MOTIVATION_QUOTES)
        channel_response = {
            'content': response_message,
            'sender': 'Motivation Channel',
            'timestamp': message['timestamp'],  
            'extra': None,
        }
        messages.append(channel_response)
        save_messages(messages)

    return "OK", 200

# Read messages from file
def read_messages():
    global CHANNEL_FILE, MAX_MESSAGES
    try:
        with open(CHANNEL_FILE, 'r') as f:
            messages = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        messages = []

    # Keep only the last MAX_MESSAGES
    if len(messages) > MAX_MESSAGES:
        messages = messages[-MAX_MESSAGES:]
    
    return messages

# Save messages to file
def save_messages(messages):
    global CHANNEL_FILE, MAX_MESSAGES
    if len(messages) > MAX_MESSAGES:
        messages = messages[-MAX_MESSAGES:]
    with open(CHANNEL_FILE, 'w') as f:
        json.dump(messages, f)

# Start the Flask application
if __name__ == '__main__':
    app.run(port=5001, debug=True)
