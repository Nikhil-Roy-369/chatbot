import sqlite3
import csv

# Path to your CSV file with custom responses
csv_path = 'data/intents_clean.csv'  # Update this if your CSV is elsewhere
sqlite_path = 'health_knowledge.db'

def seed_knowledge_base():
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()

    # Clear the table before seeding to avoid duplicates
    cursor.execute("DELETE FROM knowledge_base")

    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, quotechar='"', quoting=csv.QUOTE_MINIMAL)
        # Expecting columns: text,intent,response
        for row in reader:
            intent = row['intent']
            pattern = row['text']
            response = row.get('response')
            if not response:
                # Fallback if response column is missing or empty
                response = f"This is a placeholder response for '{pattern}' ({intent})"
            cursor.execute(
                """
                INSERT INTO knowledge_base (intent, pattern, response)
                VALUES (?, ?, ?)
                """,
                (intent, pattern, response)
            )
    conn.commit()
    conn.close()
    print("Knowledge base seeded from CSV with custom responses.")

if __name__ == "__main__":
    seed_knowledge_base()
