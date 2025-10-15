import spacy
import json
from langdetect import detect
from fuzzywuzzy import process

# Load spaCy's default English model
nlp_en = spacy.load("en_core_web_sm")

# Load your entity lists for keyword matching
with open('data/condition_entities.json', 'r', encoding='utf-8') as f:
    entities = json.load(f)

# Load your knowledge base
with open('data/condition_lookup.json', 'r', encoding='utf-8') as f:
    condition_lookup = json.load(f)

def extract_entities_hi(text):
    with open('data/condition_entities.json', 'r', encoding='utf-8') as f:
        entities = json.load(f)
    print("User input:", repr(text))
    print("Entity list:", entities["conditions_hi"])
    conditions = []
    symptoms = []
    # Exact match for conditions
    for cond in entities["conditions_hi"]:
        print("Comparing:", repr(text), "to", repr(cond))
        if text == cond:
            print("Exact match found for condition:", cond)
            conditions.append(cond)
            break
    else:
        if entities["conditions_hi"]:
            best_cond, score = process.extractOne(text, entities["conditions_hi"])
            print("Best Hindi condition match:", best_cond, "Score:", score)
            if best_cond and score >= 60:
                conditions.append(best_cond)
        else:
            print("No Hindi conditions loaded!")
    # Exact match for symptoms
    for sym in entities["symptoms_hi"]:
        if text == sym:
            print("Exact match found for symptom:", sym)
            symptoms.append(sym)
            break
    else:
        if entities["symptoms_hi"]:
            best_sym, score = process.extractOne(text, entities["symptoms_hi"])
            print("Best Hindi symptom match:", best_sym, "Score:", score)
            if best_sym and score >= 60:
                symptoms.append(best_sym)
        else:
            print("No Hindi symptoms loaded!")
    return list(set(conditions)), list(set(symptoms))

def extract_entities_en(text):
    with open('data/condition_entities.json', 'r', encoding='utf-8') as f:
        entities = json.load(f)
    doc = nlp_en(text)
    conditions = []
    symptoms = []
    for cond in entities["conditions_en"]:
        if cond.lower() in text.lower():
            conditions.append(cond)
    for sym in entities["symptoms_en"]:
        if sym.lower() in text.lower():
            symptoms.append(sym)
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PERSON", "GPE"]:
            conditions.append(ent.text)
    return list(set(conditions)), list(set(symptoms))

# Multi-turn session context
session_context = {}

def update_context(conds, syms):
    if conds:
        session_context['condition'] = conds[0]
    if syms:
        session_context['symptoms'] = syms

def get_condition_info_from_json(condition, lang="en"):
    info = condition_lookup.get(condition)
    if info:
        return info
    if lang == "en":
        info = condition_lookup.get(condition.lower())
        if info:
            return info
        info = condition_lookup.get(condition.title())
        if info:
            return info
    return None

def generate_response(lang="en"):
    if 'condition' in session_context:
        info = get_condition_info_from_json(session_context['condition'], lang=lang)
        if info:
            if lang == "hi":
                response = (
                    f"**{info['condition_hi']}**\n"
                    f"{info['description_hi']}\n"
                    f"\nलक्षण: {info['possible_symptom_hi']}\n"
                    f"\nप्राथमिक उपचार: {info['first_aid_tips_hi']}\n"
                    f"\nरोकथाम: {info['prevention_tips_hi']}\n"
                    f"\n{info['disclaimer_hi']}"
                )
            else:
                response = (
                    f"**{info['condition_en']}**\n"
                    f"{info['description_en']}\n"
                    f"\nSymptoms: {info['possible_symptom_en']}\n"
                    f"\nFirst aid: {info['first_aid_tips_en']}\n"
                    f"\nPrevention: {info['prevention_tips_en']}\n"
                    f"\n{info['disclaimer_en']}"
                )
            return response
        else:
            return "माफ़ कीजिए, मुझे उस स्थिति के बारे में जानकारी नहीं मिली।" if lang == "hi" else "Sorry, I couldn't find information about that condition."
    else:
        return None

if __name__ == "__main__":
    print("Multilingual Health Chatbot (type 'exit' to quit)")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        # Detect language
        lang = detect(user_input)
        if lang not in ["en", "hi"]:
            lang = "en"

        # Entity extraction
        if lang == "en":
            conds, syms = extract_entities_en(user_input)
        else:
            conds, syms = extract_entities_hi(user_input)

        # Slot filling
        update_context(conds, syms)

        # Multi-turn: Ask for missing info
        if 'condition' not in session_context:
            print("Bot:", "Can you tell me the condition or symptom you are experiencing?")
            continue

        # Generate and print response
        bot_response = generate_response(lang=lang)
        if bot_response:
            print("Bot:", bot_response)
        else:
            print("Bot:", "Can you provide more details about your health concern?")