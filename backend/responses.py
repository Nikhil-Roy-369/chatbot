import sqlite3
import os
import difflib

DB_PATH = os.path.join(os.path.dirname(__file__), 'health_knowledge.db')

def get_response(intent, user_message=None, min_similarity=0.7):
    """
    Fetches the response for a given intent and user_message from the SQLite knowledge base.
    Matching order: exact match, partial (substring) match, fuzzy match, fallback to first intent response.
    Returns the response string if found, else a default message.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    response = None
    try:
        if user_message:
            # 1. Exact match (case-insensitive)
            cursor.execute("""
                SELECT response FROM knowledge_base
                WHERE intent = ? AND pattern = ?
                COLLATE NOCASE
                LIMIT 1
            """, (intent, user_message))
            row = cursor.fetchone()
            if row:
                response = row[0]
                return response

            # 2. Partial (substring) match (case-insensitive)
            cursor.execute("""
                SELECT pattern, response FROM knowledge_base
                WHERE intent = ?
                COLLATE NOCASE
            """, (intent,))
            rows = cursor.fetchall()
            for pattern, resp in rows:
                if user_message.lower() in pattern.lower() or pattern.lower() in user_message.lower():
                    response = resp
                    return response

            # 3. Fuzzy match using difflib
            best_match = None
            best_score = 0.0
            for pattern, resp in rows:
                score = difflib.SequenceMatcher(None, user_message.lower(), pattern.lower()).ratio()
                if score > best_score:
                    best_score = score
                    best_match = resp
            if best_score >= min_similarity and best_match:
                response = best_match
                return response

        # 4. Fallback: return the first response for the intent
        cursor.execute("""
            SELECT response FROM knowledge_base
            WHERE intent = ?
            COLLATE NOCASE
            LIMIT 1
        """, (intent,))
        row = cursor.fetchone()
        if row:
            response = row[0]
    finally:
        conn.close()
    if response:
        return response
    return "Sorry, I don't have an answer for that yet."
