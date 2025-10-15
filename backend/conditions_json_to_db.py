import json
import sqlite3

with open('data/condition_lookup.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

conn = sqlite3.connect('health_knowledge.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS conditions (
    condition_en TEXT,
    condition_hi TEXT,
    description_en TEXT,
    description_hi TEXT,
    possible_symptom_en TEXT,
    possible_symptom_hi TEXT,
    first_aid_tips_en TEXT,
    first_aid_tips_hi TEXT,
    prevention_tips_en TEXT,
    prevention_tips_hi TEXT,
    disclaimer_en TEXT,
    disclaimer_hi TEXT,
    PRIMARY KEY (condition_en, condition_hi)
)
''')

for key, entry in data.items():
    cursor.execute('''
        INSERT OR REPLACE INTO conditions
        (condition_en, condition_hi, description_en, description_hi,
         possible_symptom_en, possible_symptom_hi, first_aid_tips_en, first_aid_tips_hi,
         prevention_tips_en, prevention_tips_hi, disclaimer_en, disclaimer_hi)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        entry['condition_en'],
        entry['condition_hi'],
        entry['description_en'],
        entry['description_hi'],
        entry['possible_symptom_en'],
        entry['possible_symptom_hi'],
        entry['first_aid_tips_en'],
        entry['first_aid_tips_hi'],
        entry['prevention_tips_en'],
        entry['prevention_tips_hi'],
        entry['disclaimer_en'],
        entry['disclaimer_hi']
    ))

conn.commit()
conn.close()
print("Data inserted into 'conditions' table in health_knowledge.db (English & Hindi fields)")