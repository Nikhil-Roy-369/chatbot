import sqlite3


# Bulk generate entries from intents_clean.csv
import csv
import os

csv_path = os.path.join('data', 'intents_clean.csv')
entries = []
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        pattern = row['text'].strip()
        intent = row['intent'].strip()
        # Placeholder response for each unique (intent, pattern)
        response = f"[Auto-generated] Response for intent '{intent}' and pattern '{pattern}'. Please customize."
        entries.append({'intent': intent, 'pattern': pattern, 'response': response})

def add_entries_to_knowledge_base(entries):
    conn = sqlite3.connect('health_knowledge.db')
    cursor = conn.cursor()
    for entry in entries:
        cursor.execute('''
            INSERT INTO knowledge_base (intent, pattern, response)
            VALUES (?, ?, ?)
        ''', (entry['intent'], entry['pattern'], entry['response']))
    conn.commit()
    conn.close()
    print(f"Added {len(entries)} entries to knowledge_base.")

if __name__ == "__main__":
    add_entries_to_knowledge_base(entries)
