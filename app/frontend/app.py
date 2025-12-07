import json
import os
import sys
import datetime
import hashlib
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "app"))

# Import process_query
from app.core.query_processor import process_query

# Import SQL tool
from app.tools.sql import query_institutions

# Import title generator
from app.frontend.title_generator import generate_conversation_title

# Import query classifier
from app.frontend.query_classifier import needs_database_results

app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / 'app' / 'frontend' / 'templates'),
    static_folder=str(PROJECT_ROOT / 'app' / 'frontend' / 'static')
)
app.secret_key = 'super_secret_key_change_this_in_production' # Needed for session

# Files - paths relative to project root
DB_FILE = PROJECT_ROOT / 'data' / 'chat.json'
USERS_FILE = PROJECT_ROOT / 'data' / 'users.json'

# --- Auth Helpers ---

def load_users():
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_users(users):
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
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
    if not DB_FILE.exists():
        return {'conversations': [], 'messages': []}
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {'conversations': [], 'messages': []}

def save_db(data):
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

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
        
        # Generate title based on user message
        # Generate title immediately for new conversations
        try:
            title = generate_conversation_title(message_content)
        except Exception as e:
            # Fallback: use first 50 chars if generation fails
            print(f"Error generating title: {e}")
            title = message_content[:50] + "..." if len(message_content) > 50 else message_content
        
        conversation = {
            'id': new_id,
            'title': title,
            'owner': current_user, # Bind to user
            'created_at': datetime.datetime.now().isoformat()
        }
        db['conversations'].append(conversation)
        conversation_id = new_id
    else:
        # Verify ownership for existing conversation
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
    
    # Extrage istoricul conversației pentru context (exclude mesajul curent care tocmai a fost adăugat)
    conversation_history = [
        {'role': m['role'], 'content': m['content']} 
        for m in db.get('messages', []) 
        if m['conversation_id'] == conversation_id and m['timestamp'] != timestamp
    ]
    
    # Process query using OpenAI and SQL tool
    try:
        # Verifică dacă query-ul necesită rezultate din baza de date
        needs_db = needs_database_results(message_content)
        
        if needs_db:
            # Pentru întrebări legate de locație: doar rezultate din baza de date, fără rezumat
            sql_response = query_institutions(message_content, 
                                             vector_store_output=None,
                                             conversation_history=conversation_history)
            
            ai_response = f"""📍 REZULTATE INSTITUȚII

{sql_response}"""
        else:
            # Pentru restul întrebărilor: doar rezumat, fără rezultate din baza de date
            vector_store_response = process_query(message_content, conversation_history=conversation_history)
            ai_response = vector_store_response
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
    
    # Get current conversation title
    updated_conv = next((c for c in db['conversations'] if c['id'] == conversation_id), None)
    conversation_title = updated_conv['title'] if updated_conv else None

    return jsonify({
        'conversation_id': conversation_id,
        'user_message': message_content,
        'ai_message': ai_response,
        'conversation_title': conversation_title
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
    
    save_db(db)
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
