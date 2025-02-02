from flask import Flask, request, jsonify
import json
import requests

# Flask App for problem solver
app = Flask(__name__)

# Konfiguration
HUB_URL = 'http://localhost:5555'
HUB_AUTHKEY = '1234567890'
CHANNEL_AUTHKEY = '1122334455' 
CHANNEL_NAME = "Problem Solver Channel"
CHANNEL_ENDPOINT = "http://localhost:5002"  
CHANNEL_TYPE_OF_SERVICE = 'aiweb24:problemsolver'

#welcome message that is sended at the begin
WELCOMES_MESSAGE_PS = "Welcome to the Problem Solver Channel! You can't find a solution to your problem ? Share your problem, and let's find solutions together. Your insights might also help others—let’s support each other!"
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
    if 'Authorization' not in request.headers:
        return False
    if request.headers['Authorization'] != 'authkey ' + CHANNEL_AUTHKEY:
        return False
    return True

@app.route('/health', methods=['GET'])
def health_check():
    if not check_authorization(request):
        return "Invalid authorization", 400
    return jsonify({'name': CHANNEL_NAME}), 200

@app.route('/', methods=['GET'])
def home_page():
    if not check_authorization(request):
        return "Invalid authorization", 400
    return jsonify(read_messages())

@app.route('/', methods=['POST'])
def send_message():
    if not check_authorization(request):
        return "Invalid authorization", 400
    
    message = request.json
    if not message or 'content' not in message or 'sender' not in message or 'timestamp' not in message:
        return "Invalid message", 400
    
    extra = message.get('extra', None)

    messages = read_messages()
    messages.append({
        'content': message['content'],
        'sender': message['sender'],
        'timestamp': message['timestamp'],
        'extra': extra,
    })
    save_messages(messages)

    #sends welcome message 
    user_messages = [msg for msg in messages if msg['sender'] == message['sender']]
    if len(user_messages) == 1:
        welcome_message = {
            'content': WELCOMES_MESSAGE_PS,
            'sender': 'ProblemSolverBot',
            'timestamp': message['timestamp'],
            'extra': None,
        }
        messages.append(welcome_message)
        save_messages(messages)

    #response to problem message
    if message['content'].lower().startswith("problem:"):
        response_message = random.choice(PROBLEM_SOLVER_RESPONSE)
        bot_response = {
            'content': response_message,
            'sender': 'ProblemSolverBot',
            'timestamp': message['timestamp'],
            'extra': None,
        }
        messages.append(bot_response)
        save_messages(messages)

    return "OK", 200

def read_messages():
    global CHANNEL_FILE, WELCOMES_MESSAGE_PS
    try:
        with open(CHANNEL_FILE, 'r') as f:
            messages = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        messages = []

    #if the welcome message doesnt already exists,it sends the welcome message 
    if not any(msg['content'] == WELCOMES_MESSAGE_PS for msg in messages):
        messages.insert(0, {
            'content': WELCOMES_MESSAGE_PS,
            'sender': 'ProblemSolverBot',
            'timestamp': 0,
            'extra': None
        })
        save_messages(messages)

    return messages

def save_messages(messages):
    global CHANNEL_FILE
    with open(CHANNEL_FILE, 'w') as f:
        json.dump(messages, f)

if __name__ == '__main__':
    app.run(port=5002, debug=True)
