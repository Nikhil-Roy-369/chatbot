
from langdetect import detect
from db import save_failed_query
from multilingual_health_chatbot import extract_entities_en, extract_entities_hi


import sqlite3

def get_condition_info_from_db(condition, lang="en"):
    print(f"[DEBUG] Looking up condition in DB: '{condition}' (lang={lang})")
    conn = sqlite3.connect('health_knowledge.db')
    cursor = conn.cursor()
    # Try exact match in English
    cursor.execute("SELECT * FROM conditions WHERE condition_en = ?", (condition,))
    row = cursor.fetchone()
    if not row and lang == "hi":
        # Try exact match in Hindi
        cursor.execute("SELECT * FROM conditions WHERE condition_hi = ?", (condition,))
        row = cursor.fetchone()
    conn.close()
    if row:
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        info = dict(zip(columns, row))
        print("[DEBUG] Found match in DB.")
        return info
    print("[DEBUG] No match found in DB.")
    return None

def get_chatbot_response(user_input, user_id=None):
    lang = detect(user_input)
    print(f"[DEBUG] Detected language: {lang}")
    if lang not in ["en", "hi"]:
        lang = "en"
    if lang == "en":
        print("[DEBUG] Using English entity extraction.")
        conds, syms = extract_entities_en(user_input)
    else:
        print("[DEBUG] Using Hindi entity extraction.")
        conds, syms = extract_entities_hi(user_input)
    if not conds:
        # Log failed query
        save_failed_query(user_id, user_input)
        return "Can you tell me the condition or symptom you are experiencing?" if lang == "en" else "कृपया अपनी स्वास्थ्य समस्या या लक्षण बताएं।"
    condition = conds[0]
    # Map Hindi condition to English equivalent for KB lookup
    if lang == "hi":
        try:
            from multilingual_health_chatbot import entities
            idx = entities["conditions_hi"].index(condition)
            kb_key = entities["conditions_en"][idx]
            print(f"[DEBUG] Mapped Hindi '{condition}' to English '{kb_key}' for DB lookup.")
        except Exception as e:
            print(f"[DEBUG] Could not map Hindi to English: {e}")
            kb_key = condition
        info = get_condition_info_from_db(kb_key, lang=lang)
    else:
        info = get_condition_info_from_db(condition, lang=lang)
    if info:
        if lang == "hi":
            print("[DEBUG] Formatting Hindi response.")
            response = (
                f"**{info.get('condition_hi', 'स्थिति')}**\n"
                f"{info.get('description_hi', '')}\n"
                f"\nलक्षण: {info.get('possible_symptom_hi', '')}\n"
                f"\nप्राथमिक उपचार: {info.get('first_aid_tips_hi', '')}\n"
                f"\nरोकथाम: {info.get('prevention_tips_hi', '')}\n"
                f"\n{info.get('disclaimer_hi', '')}"
            )
        else:
            print("[DEBUG] Formatting English response.")
            response = (
                f"**{info.get('condition_en', 'Unknown Condition')}**\n"
                f"{info.get('description_en', '')}\n"
                f"\nSymptoms: {info.get('possible_symptom_en', '')}\n"
                f"\nFirst aid: {info.get('first_aid_tips_en', '')}\n"
                f"\nPrevention: {info.get('prevention_tips_en', '')}\n"
                f"\n{info.get('disclaimer_en', '')}"
            )
        return response
    else:
        # Log failed query
        save_failed_query(user_id, user_input)
        return "Sorry, I couldn't find information about that condition." if lang == "en" else "माफ़ कीजिए, मुझे उस स्थिति के बारे में जानकारी नहीं मिली।"