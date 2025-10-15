import sqlite3
from datetime import datetime

def get_db():
    """Get a database connection to users.db"""
    return sqlite3.connect('users.db')

def init_db():
    """Initialize the users database"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            email TEXT,
            age INTEGER,
            location TEXT,
            phone TEXT,
            language TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def row_to_dict(row):
    """Convert a database row to a dictionary"""
    if not row:
        return None
    
    # Users table column names
    columns = ['id', 'username', 'password', 'email', 'age', 'location', 'phone', 'language']
    return {columns[i]: row[i] for i in range(len(columns))}

def get_user_by_email_or_username(email_or_username):
    """Get user by email or username"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if it's an email (contains @) or username
    if '@' in email_or_username:
        row = cursor.execute("SELECT * FROM users WHERE email = ?", (email_or_username,)).fetchone()
    else:
        row = cursor.execute("SELECT * FROM users WHERE username = ?", (email_or_username,)).fetchone()
    
    conn.close()
    return row_to_dict(row) if row else None

def init_feedback_db():
    conn = sqlite3.connect('data/feedback.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            query TEXT,
            response TEXT,
            rating TEXT,         -- 'up' or 'down'
            comment TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS failed_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            query TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_feedback(user_id, query, response, rating, comment):
    conn = sqlite3.connect('data/feedback.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO feedback (user_id, query, response, rating, comment)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, query, response, rating, comment))
    conn.commit()
    conn.close()

def save_failed_query(user_id, query, timestamp=None):
    conn = sqlite3.connect('data/feedback.db')
    c = conn.cursor()
    if not timestamp:
        timestamp = datetime.now().isoformat()
    c.execute('''
        INSERT INTO failed_queries (user_id, query, timestamp)
        VALUES (?, ?, ?)
    ''', (user_id, query, timestamp))
    conn.commit()
    conn.close()