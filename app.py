import sqlite3
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

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
            upvotes INTEGER DEFAULT 0
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
    
    conn.commit()
    conn.close()

# Run the database setup immediately when the file loads
init_db()

# --- SERVER ROUTES ---
@app.route('/')
def home():
    # This will load our high-contrast UI later
    return render_template('index.html')

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

if __name__ == '__main__':
    # Running in debug mode so it updates instantly when we save
    app.run(debug=True, port=5000)