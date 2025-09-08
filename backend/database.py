# database.py
import sqlite3
from typing import Optional

DB_PATH = "users.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            email TEXT UNIQUE,
            age INTEGER,
            location TEXT,
            phone TEXT,
            language TEXT
        )
    """)
    conn.commit()
    conn.close()

def row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row) if row else None

def get_user_by_email_or_username(identifier: str) -> Optional[sqlite3.Row]:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ? OR username = ?",
        (identifier, identifier)
    ).fetchone()
    conn.close()
    return row
