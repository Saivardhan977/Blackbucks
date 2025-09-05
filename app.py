import os
import sys
print("Python version:", sys.version)
print("Current working directory:", os.getcwd())
print("\nEnvironment variables:")
for key, value in os.environ.items():
    if 'python' in key.lower() or 'path' in key.lower() or 'flask' in key.lower():
        print(f"{key}: {value}")

print("\nTrying to import Flask...")
try:
    from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
    from datetime import datetime, timedelta
    from functools import wraps
    import os
    import json
    import sqlite3
    from flask_sqlalchemy import SQLAlchemy
    from werkzeug.security import generate_password_hash, check_password_hash
    print("All imports successful!")
except ImportError as e:
    print(f"\nError importing required packages: {e}")
    print("\nPlease install the required packages by running:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'dev-secret-key'  # Change this in production

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Simple in-memory user storage (for demo only)
USERS = {
    'admin': {
        'password': 'admin123',  # In a real app, never store plaintext passwords
        'username': 'admin'
    }
}

# Responses for the chatbot
RESPONSES = {
    # Greetings
    'hello': 'Hello! How can I help you today?',
    'hi': 'Hi there! How can I assist you?',
    'hey': 'Hey! What can I do for you?',
    'how are you': "I'm just a bot, but I'm functioning well! How can I help you?",
    'bye': 'Goodbye! Have a great day!',
    'help': 'I can help with arithmetic calculations, general knowledge questions, and more. Try asking me something!',
    
    # Time and Date
    'time': lambda: f'The current time is {datetime.now().strftime("%I:%M %p")}',
    'date': lambda: f'Today is {datetime.now().strftime("%A, %B %d, %Y")}',
    'what time is it': lambda: f'The current time is {datetime.now().strftime("%I:%M %p")}',
    "what's the date": lambda: f'Today is {datetime.now().strftime("%A, %B %d, %Y")}',
    
    # Help
    'what can you do': 'I can answer questions, perform calculations, and have basic conversations. Try asking me something!',
    'help me': 'I can help with math, general knowledge, and more. What would you like to know?',
    
    # General
    'thank you': "You're welcome!",
    'thanks': "You're welcome!",
    'ok': 'Is there anything else I can help you with?'
}

def safe_eval(expr):
    """Safely evaluate a mathematical expression"""
    import ast
    import operator as op
    
    # Supported operators
    operators = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.Pow: op.pow,
        ast.USub: op.neg
    }
    
    def _eval(node):
        if isinstance(node, ast.Num):  # number
            return node.n
        elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
            return operators[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):  # <operator> <operand>
            return operators[type(node.op)](_eval(node.operand))
        else:
            raise TypeError(node)
    
    try:
        tree = ast.parse(expr, mode='eval').body
        return _eval(tree)
    except (SyntaxError, TypeError, KeyError):
        return None

def get_bot_response(user_input):
    """Get a response from the bot based on user input"""
    if not user_input or not user_input.strip():
        return "I didn't catch that. Could you please rephrase?"
        
    user_input = user_input.lower().strip()
    current_time = datetime.now()
    
    # First, check if it's a direct arithmetic expression (e.g., "2+2" or "5 * 3")
    if any(op in user_input for op in ['+', '-', '*', '/', '^']):
        try:
            # Clean up the expression
            expr = user_input.replace(' ', '').replace('x', '*').replace('×', '*').replace('÷', '/')
            result = safe_eval(expr)
            if result is not None:
                return f"The result of {user_input} is {result}"
        except:
            pass
    
    # Then check for questions about arithmetic
    math_keywords = ['what is', 'calculate', 'compute', 'how much is', 'what\'s', 'evaluate']
    if any(keyword in user_input for keyword in math_keywords):
        # Extract the mathematical expression
        expr = user_input
        for kw in math_keywords:
            expr = expr.replace(kw, '').strip()
        
        # Clean up the expression
        expr = expr.replace(' ', '').replace('x', '*').replace('×', '*').replace('÷', '/')
        
        # Try to evaluate the expression
        try:
            result = safe_eval(expr)
            if result is not None:
                return f"The result of {expr} is {result}"
        except:
            pass
    
    # Basic question patterns and answers
    basic_qa = {
        # General Knowledge
        'capital of france': 'The capital of France is Paris.',
        'capital of italy': 'The capital of Italy is Rome.',
        'capital of japan': 'The capital of Japan is Tokyo.',
        'capital of india': 'The capital of India is New Delhi.',
        'capital of usa': 'The capital of the United States is Washington, D.C.',
        'capital of uk': 'The capital of the United Kingdom is London.',
        'capital of canada': 'The capital of Canada is Ottawa.',
        'capital of australia': 'The capital of Australia is Canberra.',
        
        # General Information
        'who is einstein': 'Albert Einstein was a German-born theoretical physicist who developed the theory of relativity.',
        'who is newton': 'Sir Isaac Newton was an English mathematician, physicist, and astronomer who formulated the laws of motion and universal gravitation.',
        'who is tesla': 'Nikola Tesla was a Serbian-American inventor and engineer known for his contributions to the design of modern alternating current electricity supply systems.',
        'who is edison': 'Thomas Edison was an American inventor and businessman who developed many devices including the phonograph and the long-lasting electric light bulb.',
        
        # Technology
        'what is python': 'Python is a high-level, interpreted programming language known for its readability and versatility.',
        'what is javascript': 'JavaScript is a programming language used to create interactive effects within web browsers.',
        'what is html': 'HTML (HyperText Markup Language) is the standard markup language for creating web pages.',
        'what is css': 'CSS (Cascading Style Sheets) is a style sheet language used for describing the presentation of a document written in HTML.',
        
        # Science
        'what is gravity': 'Gravity is a force that attracts two bodies toward each other, like the Earth pulling objects toward its center.',
        'what is photosynthesis': 'Photosynthesis is the process by which green plants use sunlight to synthesize foods with carbon dioxide and water.',
        'what is dna': 'DNA (Deoxyribonucleic Acid) is a molecule that carries genetic instructions in living organisms.',
        'what is the speed of light': 'The speed of light in a vacuum is approximately 299,792 kilometers per second (or about 186,282 miles per second).',
        
        # History
        'who was the first president of the united states': 'George Washington was the first President of the United States.',
        'when was world war 2': 'World War II was from 1939 to 1945.',
        'who discovered america': 'Christopher Columbus is often credited with discovering America in 1492, though the land was already inhabited by indigenous peoples.',
        'when was the internet created': 'The precursor to the modern Internet, ARPANET, was created in the late 1960s.',
    }
    
    # Check basic questions first
    for question, answer in basic_qa.items():
        if question in user_input:
            return answer
    
    # Define responses with more context and functionality
    RESPONSES = {
        # Greetings
        'hello': 'Hello! How can I help you today?',
        'hi': 'Hi there! How can I assist you?',
        'hey': 'Hey! What can I do for you?',
        
        # Time and Date
        'time': f'The current time is {current_time.strftime("%I:%M %p")}',
        'date': f'Today is {current_time.strftime("%A, %B %d, %Y")}',
        'day': f'Today is {current_time.strftime("%A")}',
        'what time is it': f'It\'s {current_time.strftime("%I:%M %p")}',
        'what\'s the time': f'The time is {current_time.strftime("%I:%M %p")}',
        'what is today': f'Today is {current_time.strftime("%A, %B %d, %Y")}',
        
        # About the bot
        'who are you': 'I\'m a simple chatbot designed to assist you with basic tasks and answer questions!',
        'what can you do': 'I can tell you the time and date, answer questions, and have simple conversations. Try asking me something!',
        'your name': 'I\'m SimpleChat, your friendly neighborhood chatbot!',
        'who made you': 'I was created by a developer to help with basic tasks and answer questions!',
        'what are you': 'I\'m a chatbot, an AI program designed to simulate conversation with users like you!',
        
        # Help
        'help': 'I can help with: time, date, day, and answer general questions. Try asking me things like "What time is it?" or "What day is today?"',
        'what can you help with': 'I can help with: time, date, day, and answer general questions. Just ask!',
        'what should i ask you': 'You can ask me about the time, date, general knowledge, or just chat! Try asking "What can you do?" for more ideas.',
        'how do i use you': 'Just type your question or message in the chat box and press enter. Try asking about the time, date, or anything else!',
        
        # Small talk
        'how are you': 'I\'m just a bot, but I\'m functioning well! How can I help you today?',
        'how are you doing': 'I\'m doing great, thanks for asking! How can I assist you?',
        'good morning': 'Good morning! How can I help you start your day?',
        'good afternoon': 'Good afternoon! How can I assist you?',
        'good evening': 'Good evening! How can I help you?',
        'good night': 'Good night! Sleep well!',
        'how\'s it going': 'Everything is working perfectly! How can I help you today?',
        'what\'s up': 'Not much, just here to help you! What can I do for you?',
        'how have you been': 'I\'ve been running smoothly! How about you?',
        
        # Goodbyes
        'bye': 'Goodbye! Have a great day!',
        'goodbye': 'Goodbye! Come back soon!',
        'see you': 'See you later!',
        'talk to you later': 'Sure, talk to you later!',
        'take care': 'You too! Take care!',
        'have a nice day': 'Thank you! You have a wonderful day too!',
        
        # Thanks
        'thank you': 'You\'re welcome!',
        'thanks': 'You\'re welcome!',
        'thanks a lot': 'You\'re very welcome!',
        'thank you so much': 'My pleasure! Is there anything else I can help with?',
        'i appreciate it': 'Happy to help! Let me know if you need anything else.',
        
        # General Knowledge
        'who is the president': 'I don\'t have real-time information, but you can check the latest news for current leadership information.',
        'what is the capital of': 'I can tell you that the capital of many countries! Try asking about a specific country.',
        'how old are you': 'I was just created, so I\'m brand new!',
        'where are you from': 'I exist in the digital world, ready to help users like you!',
        'what language do you speak': 'I primarily understand English, but I can handle basic phrases in other languages too!',
        
        # Technology
        'are you a robot': 'Yes, I\'m a chatbot - a program designed to simulate conversation with users!',
        'are you ai': 'Yes, I\'m an AI chatbot designed to assist with basic tasks and answer questions!',
        'do you have feelings': 'I don\'t have feelings like humans do, but I\'m here to help in any way I can!',
        'what can you tell me': 'I can share general knowledge, tell jokes, discuss the time and date, and have simple conversations!',
        
        # Weather (simple response)
        'how is the weather': 'I don\'t have real-time weather data, but I hope it\'s nice outside!',
        'what\'s the weather like': 'I can\'t check the weather right now, but I hope it\'s pleasant!',
        'is it raining': 'I don\'t have weather data, but you can check a weather app for the latest updates!',
        'will it rain today': 'I can\'t predict the weather, but I recommend checking a weather forecast!',
        
        # Jokes
        'tell me a joke': 'Why don\'t scientists trust atoms? Because they make up everything!',
        'joke': 'What do you call fake spaghetti? An impasta!',
        'make me laugh': 'Why did the scarecrow win an award? Because he was outstanding in his field!',
        'another joke': 'Why don\'t eggs tell jokes? They\'d crack each other up!',
        'tell me something funny': 'What\'s the best thing about Switzerland? I don\'t know, but the flag is a big plus!',
        
        # Fun facts
        'tell me a fact': 'A group of flamingos is called a "flamboyance".',
        'fun fact': 'Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly good to eat!',
        'interesting fact': 'Octopuses have three hearts: two pump blood to the gills, while the third pumps it to the rest of the body.',
        'did you know': 'A day on Venus is longer than a year on Venus. It takes Venus 243 Earth days to rotate once on its axis, but only 225 Earth days to orbit the Sun!',
        
        # Commands
        'clear': 'clear',  # Special command to clear chat
        'help me': 'I can help with time, date, general knowledge, and more. Try asking specific questions!',
        'what now': 'You can ask me about the time, date, or any general knowledge questions. Or we can just chat!',
        'start over': 'Sure! How can I help you today?',
        'begin again': 'Of course! What would you like to know or talk about?'
    }
    
    # Check for exact matches first
    if user_input in RESPONSES:
        response = RESPONSES[user_input]
        return response() if callable(response) else response
    
    # Check for partial matches
    for key in RESPONSES:
        if key in user_input:
            response = RESPONSES[key]
            return response() if callable(response) else response
    
    # Check for time-related questions
    if any(word in user_input for word in ['time', 'clock', 'hour', 'minute']):
        return f'The current time is {current_time.strftime("%I:%M %p")}'
        
    if any(word in user_input for word in ['date', 'today', 'day', 'month', 'year']):
        return f'Today is {current_time.strftime("%A, %B %d, %Y")}'
    
    # Default response if no match found
    return "I'm not sure how to respond to that. Type 'help' to see what I can do or ask me about the time/date!"

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        user_message = request.json.get('message')
        bot_response = get_bot_response(user_message)
        return jsonify({'response': bot_response})
    
    return render_template('chat_simple.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USERS and USERS[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('index'))
        
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Failed</title>
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500&display=swap" rel="stylesheet">
            <style>
                body {
                    font-family: 'Roboto', sans-serif;
                    background: #f5f5f5;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }
                .error-message {
                    background: #ffebee;
                    color: #c62828;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    text-align: center;
                }
                .back-button {
                    display: block;
                    text-align: center;
                    margin-top: 20px;
                    color: #1976d2;
                    text-decoration: none;
                }
            </style>
        </head>
        <body>
            <div>
                <div class="error-message">
                    Invalid username or password. Please try again.
                </div>
                <a href="/login" class="back-button">← Back to Login</a>
            </div>
        </body>
        </html>
        '''
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Simple Chat</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500&display=swap" rel="stylesheet">
        <style>
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            body {
                font-family: 'Roboto', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            .container {
                width: 100%;
                max-width: 400px;
            }
            .card {
                background: white;
                border-radius: 10px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
                overflow: hidden;
            }
            .card-header {
                background: #4a6fa5;
                color: white;
                padding: 25px;
                text-align: center;
            }
            .card-body {
                padding: 30px;
            }
            .form-group {
                margin-bottom: 20px;
            }
            .form-group label {
                display: block;
                margin-bottom: 8px;
                font-weight: 500;
                color: #555;
            }
            .form-control {
                width: 100%;
                padding: 12px 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            .form-control:focus {
                border-color: #4a6fa5;
                outline: none;
                box-shadow: 0 0 0 3px rgba(74, 111, 165, 0.2);
            }
            .btn {
                display: block;
                width: 100%;
                padding: 12px;
                background: #4a6fa5;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: 500;
                cursor: pointer;
                transition: background-color 0.3s;
            }
            .btn:hover {
                background: #3a5a80;
            }
            .divider {
                text-align: center;
                margin: 20px 0;
                position: relative;
            }
            .divider::before, .divider::after {
                content: '';
                display: inline-block;
                width: 30%;
                height: 1px;
                background: #ddd;
                position: absolute;
                top: 50%;
            }
            .divider::before {
                left: 0;
            }
            .divider::after {
                right: 0;
            }
            .divider span {
                background: white;
                padding: 0 10px;
                color: #777;
                font-size: 14px;
                position: relative;
            }
            .signup-link {
                display: block;
                text-align: center;
                margin-top: 20px;
                color: #4a6fa5;
                text-decoration: none;
                font-weight: 500;
            }
            .signup-link:hover {
                text-decoration: underline;
            }
            .demo-credentials {
                margin-top: 20px;
                padding: 15px;
                background: #f5f5f5;
                border-radius: 5px;
                font-size: 14px;
                color: #666;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2>Welcome Back!</h2>
                    <p>Login to continue to Simple Chat</p>
                </div>
                <div class="card-body
                ">
                    <form method="post">
                        <div class="form-group">
                            <label for="username">Username</label>
                            <input type="text" id="username" name="username" class="form-control" required>
                        </div>
                        <div class="form-group">
                            <label for="password">Password</label>
                            <input type="password" id="password" name="password" class="form-control" required>
                        </div>
                        <button type="submit" class="btn">Login</button>
                        <div class="divider"><span>OR</span></div>
                        <a href="/signup" class="btn" style="background: #42b72a;">Create New Account</a>
                    </form>
                    <div class="demo-credentials">
                        Demo Account:<br>
                        Username: admin<br>
                        Password: admin123
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not password or not confirm_password:
            return 'All fields are required', 400
            
        if password != confirm_password:
            return 'Passwords do not match', 400
            
        if username in USERS:
            return 'Username already exists', 400
            
        # Add new user
        USERS[username] = {
            'password': password,  # In a real app, hash the password
            'username': username
        }
        
        # Log the user in
        session['username'] = username
        return redirect(url_for('index'))
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sign Up - Simple Chat</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500&display=swap" rel="stylesheet">
        <style>
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            body {
                font-family: 'Roboto', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            .container {
                width: 100%;
                max-width: 400px;
            }
            .card {
                background: white;
                border-radius: 10px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
                overflow: hidden;
            }
            .card-header {
                background: #4a6fa5;
                color: white;
                padding: 25px;
                text-align: center;
            }
            .card-body {
                padding: 30px;
            }
            .form-group {
                margin-bottom: 20px;
            }
            .form-group label {
                display: block;
                margin-bottom: 8px;
                font-weight: 500;
                color: #555;
            }
            .form-control {
                width: 100%;
                padding: 12px 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            .form-control:focus {
                border-color: #4a6fa5;
                outline: none;
                box-shadow: 0 0 0 3px rgba(74, 111, 165, 0.2);
            }
            .btn {
                display: block;
                width: 100%;
                padding: 12px;
                background: #4a6fa5;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: 500;
                cursor: pointer;
                transition: background-color 0.3s;
            }
            .btn:hover {
                background: #3a5a80;
            }
            .login-link {
                display: block;
                text-align: center;
                margin-top: 20px;
                color: #4a6fa5;
                text-decoration: none;
                font-weight: 500;
            }
            .login-link:hover {
                text-decoration: underline;
            }
            .password-requirements {
                font-size: 12px;
                color: #666;
                margin-top: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2>Create Account</h2>
                    <p>Join Simple Chat today</p>
                </div>
                <div class="card-body">
                    <form method="post">
                        <div class="form-group">
                            <label for="username">Choose a Username</label>
                            <input type="text" id="username" name="username" class="form-control" required>
                        </div>
                        <div class="form-group">
                            <label for="password">Create Password</label>
                            <input type="password" id="password" name="password" class="form-control" required>
                            <div class="password-requirements">Use at least 6 characters</div>
                        </div>
                        <div class="form-group">
                            <label for="confirm_password">Confirm Password</label>
                            <input type="password" id="confirm_password" name="confirm_password" class="form-control" required>
                        </div>
                        <button type="submit" class="btn">Create Account</button>
                    </form>
                    <a href="/login" class="login-link">Already have an account? Login</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/get_response', methods=['POST'])
def get_response():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
        
    user_message = request.json.get('message')
    bot_response = get_bot_response(user_message)
    return jsonify({'response': bot_response})

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    if request.method == 'POST' and request.is_json:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if user_message:
            # Get response from ChatGPT
            bot_response = get_bot_response(str(current_user.id), user_message)
            
            # Save the message and response to the database
            message = Message(
                content=user_message,
                response=bot_response,
                user_id=current_user.id,
                timestamp=datetime.utcnow()
            )
            db.session.add(message)
            db.session.commit()
            
            return jsonify({'response': bot_response})
    
    # For GET requests, show the chat interface
    return render_template('chat.html')

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        # Handle settings update
        current_user.email = request.form.get('email')
        # Add more settings as needed
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html')

@app.route('/split_chat')
@login_required
def split_chat():
    """Render the split view chat interface"""
    return render_template('split_chat.html')

def init_db():
    with app.app_context():
        try:
            # Create the instance directory if it doesn't exist
            instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
            if not os.path.exists(instance_path):
                os.makedirs(instance_path)
                print(f"Created instance directory at {instance_path}")
            
            # Create database tables if they don't exist
            print("Creating database tables...")
            db.create_all()
            
            # Create admin user if it doesn't exist
            if not User.query.filter_by(username='admin').first():
                print("Creating admin user...")
                admin = User(
                    username='admin',
                    is_admin=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("Created default admin user with username 'admin' and password 'admin123'")
            else:
                print("Admin user already exists")
                
            return True
            
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("Starting application initialization...")
    if init_db():
        print("Database initialized successfully. Starting Flask application...")
        app.run(debug=True, use_reloader=False)  # Disable reloader to prevent duplicate execution
    else:
        print("Failed to initialize database. Please check the error message above.")
