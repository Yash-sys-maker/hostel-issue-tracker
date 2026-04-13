import sqlite3
from flask import Flask, request, jsonify, render_template, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'super_secret_hostel_key'

# --- DATABASE SETUP ---
def init_db():
    """Creates the SQLite database tables if they don't exist yet."""
    conn = sqlite3.connect('hostel_issues.db')
    cursor = conn.cursor()
    
    # Table 1: Issues (Existing)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            upvotes INTEGER DEFAULT 0,
                   status TEXT DEFAULT 'open'
        )
    ''')
    
    # Table 2: Users (The Upgrade!)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            user_id INTEGER,
            issue_id INTEGER,
            UNIQUE(user_id, issue_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Run the database setup immediately when the file loads
init_db()

# --- SERVER ROUTES ---
@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    
    return render_template('index.html', 
                           username=session['username'], 
                           role=session['role'])

@app.route('/add_issue', methods=['POST'])
def add_issue():
    # Receive the data sent by the JavaScript we wrote earlier
    data = request.json
    room = data.get('room')
    title = data.get('title')
    desc = data.get('desc')

    # Save it into our SQLite database
    conn = sqlite3.connect('hostel_issues.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO issues (room_number, title, description) VALUES (?, ?, ?)', 
                   (room, title, desc))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Issue added to database!"})

@app.route('/get_issues')
def get_issues():
    conn = sqlite3.connect('hostel_issues.db')
    # This 'row_factory' line makes the data easier for JavaScript to read
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    # We sort by upvotes (descending) so the most important issues stay at the top
    cursor.execute('SELECT * FROM issues ORDER BY upvotes DESC')
    rows = cursor.fetchall()
    
    # Convert the database rows into a list of dictionaries
    issues = [dict(row) for row in rows]
    conn.close()
    
    return jsonify(issues)


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/register_page')
def register_page():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password') # In V2, we will hash this for security!
    role = data.get('role')

    try:
        conn = sqlite3.connect('hostel_issues.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', 
                       (username, password, role))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "Username already exists!"}), 400

@app.route('/login_action', methods=['POST'])
def login_action():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = sqlite3.connect('hostel_issues.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if the user exists
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        # Save the user info in a "Session" cookie
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        return jsonify({"status": "success", "role": user['role']})
    else:
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route('/logout')
def logout():
    session.clear() # This wipes the cookie
    return redirect(url_for('login_page'))

@app.route('/resolve_issue/<int:issue_id>', methods=['POST'])
def resolve_issue(issue_id):
    # Security Check: Only Admins can resolve
    if session.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    conn = sqlite3.connect('hostel_issues.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE issues SET status = "resolved" WHERE id = ?', (issue_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/upvote_issue/<int:issue_id>', methods=['POST'])
def upvote_issue(issue_id):
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Login to upvote"}), 401

    user_id = session['user_id']
    conn = sqlite3.connect('hostel_issues.db')
    cursor = conn.cursor()

    try:
        # 1. Try to record this specific user's vote for this specific issue
        cursor.execute('INSERT INTO votes (user_id, issue_id) VALUES (?, ?)', (user_id, issue_id))
        
        # 2. If the line above worked, increment the count
        cursor.execute('UPDATE issues SET upvotes = upvotes + 1 WHERE id = ?', (issue_id,))
        
        conn.commit()
        return jsonify({"status": "success"})
    
    except sqlite3.IntegrityError:
        # This error happens if the (user_id, issue_id) pair already exists
        return jsonify({"status": "error", "message": "You have already upvoted this!"}), 400
    
    finally:
        conn.close()
        

if __name__ == '__main__':
    # Running in debug mode so it updates instantly when we save
    app.run(debug=True, port=5000)