import sqlite3
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# --- DATABASE SETUP ---
def init_db():
    """Creates the SQLite database table if it doesn't exist yet."""
    conn = sqlite3.connect('hostel_issues.db')
    cursor = conn.cursor()
    # Create our high-performance table for the issues
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            upvotes INTEGER DEFAULT 0
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

if __name__ == '__main__':
    # Running in debug mode so it updates instantly when we save
    app.run(debug=True, port=5000)