import json
import os
import sys
import datetime
import hashlib
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import process_query after adding parent to path
from main import process_query

# Import SQL tool
from src.tools.sql import query_institutions

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this_in_production' # Needed for session

# Files
DB_FILE = 'chat.json'
USERS_FILE = 'users.json'

# --- Auth Helpers ---

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def create_user(username, password):
    users = load_users()
    if username in users:
        return False
    
    users[username] = {
        "password_hash": hash_password(password),
        "created_at": datetime.datetime.now().isoformat()
    }
    save_users(users)
    return True

def verify_user(username, password):
    users = load_users()
    if username not in users:
        return False
    stored_hash = users[username]["password_hash"]
    input_hash = hash_password(password)
    return stored_hash == input_hash

# --- Decorators ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Chat DB Helpers ---

def load_db():
    if not os.path.exists(DB_FILE):
        return {'conversations': [], 'messages': []}
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {'conversations': [], 'messages': []}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- Routes ---

@app.route('/')
@login_required
def index():
    return render_template('index.html', username=session['username'])

# Auth Routes

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if verify_user(username, password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid username or password")
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if password != confirm:
            return render_template('register.html', error="Passwords do not match")
        
        if create_user(username, password):
            # Optional: Auto login
            # session['username'] = username
            # return redirect(url_for('index'))
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error="Username already exists")
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# API Routes

@app.route('/api/conversations', methods=['GET'])
@login_required
def get_conversations():
    db = load_db()
    # Filter by user if we were separating them. For now global or global.
    # To separate: filter by session['username'] if we added owner field.
    # The requirement didn't specify per-user memory, just auth system.
    # We will keep it shared for simplicity unless asked, but typically it should be private.
    # Let's add 'owner' field to new conversations.
    current_user = session['username']
    
    all_Convs = db.get('conversations', [])
    # Filter if they have 'owner' field; if not (legacy), show to all? or hide?
    # Let's show only those owned by user OR legacy ones without owner (optional)
    # Better: just show ones matching owner.
    
    user_convs = [c for c in all_Convs if c.get('owner') == current_user]
    
    # If using legacy data without owners, maybe we just show empty for now or claim them?
    # Let's just stick to the filter.
    
    conversations = sorted(user_convs, key=lambda x: x['id'], reverse=True)
    return jsonify(conversations)

@app.route('/api/conversations/<int:conversation_id>', methods=['GET'])
@login_required
def get_messages(conversation_id):
    db = load_db()
    # Check ownership?
    conv = next((c for c in db.get('conversations', []) if c['id'] == conversation_id), None)
    if not conv:
        return jsonify([])
    
    if conv.get('owner') and conv['owner'] != session['username']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    messages = [m for m in db.get('messages', []) if m['conversation_id'] == conversation_id]
    return jsonify(messages)

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    message_content = data.get('message')
    conversation_id = data.get('conversation_id')
    current_user = session['username']
    
    if not message_content:
        return jsonify({'error': 'Message content required'}), 400

    db = load_db()
    
    # Create new conversation if none exists
    if not conversation_id:
        max_id = 0
        if db['conversations']:
            max_id = max(c['id'] for c in db['conversations'])
        
        new_id = max_id + 1
        
        # Calculate Title Index relative to User
        user_convs = [c for c in db['conversations'] if c.get('owner') == current_user]
        # Regex to find max "Chat N" could be safer, but simpler: count + 1
        # To avoid duplicates if some are deleted, let's just count total ever created? No data for that.
        # Let's verify if "Chat X" exists, if so increment.
        chat_num = len(user_convs) + 1
        while any(c['title'] == f"Consultare {chat_num}" for c in user_convs):
            chat_num += 1
            
        title = f"Consultare {chat_num}"
        
        conversation = {
            'id': new_id,
            'title': title,
            'owner': current_user, # Bind to user
            'created_at': datetime.datetime.now().isoformat()
        }
        db['conversations'].append(conversation)
        conversation_id = new_id
    else:
        # Verify ownership
        conv = next((c for c in db['conversations'] if c['id'] == conversation_id), None)
        if conv and conv.get('owner') and conv['owner'] != current_user:
             return jsonify({'error': 'Unauthorized'}), 403
    
    timestamp = datetime.datetime.now().isoformat()

    # Save User message
    user_msg = {
        'conversation_id': conversation_id,
        'role': 'user',
        'content': message_content,
        'timestamp': timestamp
    }
    db['messages'].append(user_msg)
    
    # Process query using OpenAI and SQL tool
    try:
        # Rulează main.py pentru a obține rezultatele din vector store
        vector_store_response = process_query(message_content)
        
        # Apoi rulează query-ul SQL (pasează output-ul pentru a evita dublarea)
        sql_response = query_institutions(message_content, vector_store_output=vector_store_response)
        
        # Combină ambele răspunsuri
        ai_response = f"""{vector_store_response}

{'='*70}
📍 REZULTATE INSTITUȚII
{'='*70}

{sql_response}"""
    except Exception as e:
        ai_response = f"❌ Eroare la procesarea întrebării: {str(e)}"
    
    ai_msg = {
        'conversation_id': conversation_id,
        'role': 'assistant',
        'content': ai_response,
        'timestamp': timestamp
    }
    db['messages'].append(ai_msg)
    
    save_db(db)

    return jsonify({
        'conversation_id': conversation_id,
        'user_message': message_content,
        'ai_message': ai_response
    })

@app.route('/api/conversations/<int:conversation_id>', methods=['DELETE'])
@login_required
def delete_conversation(conversation_id):
    db = load_db()
    current_user = session['username']
    
    # 1. Check if conversation exists and belongs to user
    conv_to_delete = next((c for c in db['conversations'] if c['id'] == conversation_id), None)
    
    if not conv_to_delete:
        return jsonify({'error': 'Conversation not found'}), 404
        
    if conv_to_delete.get('owner') and conv_to_delete['owner'] != current_user:
        return jsonify({'error': 'Unauthorized'}), 403
        
    # 2. Remove conversation
    db['conversations'] = [c for c in db['conversations'] if c['id'] != conversation_id]
    
    # 3. Remove messages associated with it
    db['messages'] = [m for m in db['messages'] if m['conversation_id'] != conversation_id]
    
    # 4. Re-index User's conversations
    all_conversations = db['conversations']
    user_convs = sorted([c for c in all_conversations if c.get('owner') == current_user], key=lambda x: x['id'])
    
    for index, conv in enumerate(user_convs):
        conv['title'] = f"Consultare {index + 1}"
    
    save_db(db)
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
