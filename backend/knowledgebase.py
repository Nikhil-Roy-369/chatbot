import sqlite3

# Connect (this will create the DB file if it doesn’t exist)
conn = sqlite3.connect("health_knowledge.db")
cursor = conn.cursor()

# Create the knowledge_base table (only once)
cursor.execute("""
CREATE TABLE IF NOT EXISTS knowledge_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intent TEXT NOT NULL,
    pattern TEXT,
    response TEXT NOT NULL
)
""")


conn.commit()
conn.close()

# --- Knowledge base query function ---
def get_knowledge_response(intent, query=None):
    conn = sqlite3.connect('health_knowledge.db')
    cursor = conn.cursor()
    if query:
        cursor.execute('SELECT response FROM knowledge_base WHERE intent=? AND pattern=?', (intent, query))
        row = cursor.fetchone()
        if row:
            conn.close()
            return row[0]
    # fallback: get any response for the intent
    cursor.execute('SELECT response FROM knowledge_base WHERE intent=?', (intent,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None
