import streamlit as st
import sqlite3
import pandas as pd
import json
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Admin Dashboard", layout="wide")

# --- Simple login ---
def login():
    st.title("Admin Dashboard")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if pw == "admin123":  # Change this to your real password
            st.session_state["logged_in"] = True
        else:
            st.error("Wrong password!")

if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    login()
    st.stop()

# --- Connect to DBs (use absolute path) ---
fb_conn = sqlite3.connect("c:/Users/NIKHIL/Desktop/chatbot-summary-ai/backend/data/feedback.db")
kb_conn = sqlite3.connect("c:/Users/NIKHIL/Desktop/chatbot-summary-ai/backend/health_knowledge.db")

df = pd.read_sql_query("SELECT * FROM feedback ORDER BY timestamp DESC", fb_conn)

# --- Helper: Sync JSON from DB ---
def sync_kb_json_from_db(kb_conn):
    df_kb = pd.read_sql_query("SELECT * FROM conditions", kb_conn)
    kb_dict = {}
    for _, row in df_kb.iterrows():
        kb_dict[row['condition_en']] = {k: row[k] for k in df_kb.columns if k != 'condition_en'}
    with open("c:/Users/NIKHIL/Desktop/chatbot-summary-ai/backend/data/condition_lookup.json", "w", encoding="utf-8") as f:
        json.dump(kb_dict, f, ensure_ascii=False, indent=2)
    return kb_dict

def update_condition_entities_json(kb_conn):
    df_kb = pd.read_sql_query("SELECT condition_en, condition_hi, possible_symptom_en, possible_symptom_hi FROM conditions", kb_conn)
    entities = {
        "conditions_en": sorted(df_kb["condition_en"].dropna().unique().tolist()),
        "conditions_hi": sorted(df_kb["condition_hi"].dropna().unique().tolist()),
        "symptoms_en": sorted(set(s.strip() for s in df_kb["possible_symptom_en"].dropna().str.split(",").sum())),
        "symptoms_hi": sorted(set(s.strip() for s in df_kb["possible_symptom_hi"].dropna().str.split(",").sum())),
    }
    with open("c:/Users/NIKHIL/Desktop/chatbot-summary-ai/backend/data/condition_entities.json", "w", encoding="utf-8") as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)
    return entities

# --- Stat Cards ---
st.markdown("## 📊 Dashboard Overview")
col1, col2, col3, col4 = st.columns(4)
total_users = df['user_id'].nunique() if not df.empty else 0
total_queries = len(df)
health_topics = pd.read_sql_query("SELECT COUNT(*) as cnt FROM conditions", kb_conn)["cnt"].iloc[0]
pos = (df['rating'] == 'up').sum()
neg = (df['rating'] == 'down').sum()
total_fb = pos + neg
pos_percent = (pos / total_fb * 100) if total_fb > 0 else 0

col1.metric("Total Users", total_users)
col2.metric("Queries Handled", total_queries)
col3.metric("Health Topics", health_topics)
col4.metric("Positive Feedback", f"{pos_percent:.1f}%")

st.markdown("---")

# --- Analytics Section ---
with st.expander("📈 Analytics", expanded=True):
    if not df.empty:
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        trend = df.groupby('date').size().reset_index(name='count')
        fig = px.line(trend, x='date', y='count', title='Query Trends Over Time')
        st.plotly_chart(fig, use_container_width=True)

        # Feedback pie chart
        pie = px.pie(
            names=["Positive", "Negative"],
            values=[pos, neg],
            color_discrete_sequence=["#4CAF50", "#F44336"],
            title="Feedback Distribution"
        )
        st.plotly_chart(pie, use_container_width=True)

        # Top queries (by query text)
        top_queries = df['query'].value_counts().head(10)
        st.subheader("🏆 Top  Queries")
        st.bar_chart(top_queries)

        # Download Feedback CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download Feedback CSV", csv, "feedback.csv", "text/csv")

        # Search/filter feedback
        st.subheader("🔍 Search Feedback")
        search = st.text_input("Search by query or comment")
        if search:
            filtered_df = df[df['query'].str.contains(search, case=False, na=False) | df['comment'].str.contains(search, case=False, na=False)]
            st.dataframe(filtered_df)
        else:
            st.dataframe(df)

        # Alert for high negative feedback
        st.subheader("⚠️ Alerts")
        neg_threshold = 3  # Set your threshold
        neg_counts = df[df['rating'] == 'down']['response'].value_counts()
        for resp, count in neg_counts.items():
            if count >= neg_threshold:
                st.warning(f"Response '{resp[:40]}...' received {count} negative feedbacks!")
    else:
        st.info("No feedback data yet.")

# --- Recent Feedback Section ---
with st.expander("📝 Recent Feedback", expanded=False):
    if not df.empty:
        def feedback_badge(rating):
            color = "#4CAF50" if rating == "up" else "#F44336"
            icon = "👍" if rating == "up" else "👎"
            return f"<span style='color:{color};font-size:1.2em'>{icon}</span>"
        for _, row in df.head(5).iterrows():
            st.markdown(f"{feedback_badge(row['rating'])} {row['comment']} <span style='color:#888'>({row['timestamp']})</span>", unsafe_allow_html=True)
    else:
        st.info("No feedback yet.")

# --- Knowledge Base Table ---
with st.expander("📚 Knowledge Base Table", expanded=False):
    kb_df = pd.read_sql_query("SELECT * FROM conditions", kb_conn)
    kb_table = kb_df[["condition_en", "description_en"]].rename(
        columns={"condition_en": "Condition", "description_en": "Description"}
    )
    kb_search = st.text_input("Search KB")
    if kb_search:
        kb_table = kb_table[kb_table["Condition"].str.contains(kb_search, case=False, na=False)]
    st.dataframe(kb_table)

# --- Knowledge Base Management ---
with st.expander("🛠️ Knowledge Base Management", expanded=False):
    kb_df = pd.read_sql_query("SELECT * FROM conditions", kb_conn)
    kb_keys = kb_df['condition_en'].tolist()
    selected = st.selectbox("Select a KB entry to edit/delete", kb_keys)
    if selected:
        entry = kb_df[kb_df['condition_en'] == selected].iloc[0]
        with st.form("edit_kb"):
            condition_en = st.text_input("Condition (EN)", entry['condition_en'] or "")
            condition_hi = st.text_input("Condition (HI)", entry['condition_hi'] or "")
            description_en = st.text_area("Description (EN)", entry['description_en'] or "")
            description_hi = st.text_area("Description (HI)", entry['description_hi'] or "")
            possible_symptom_en = st.text_area("Possible Symptoms (EN)", entry['possible_symptom_en'] or "")
            possible_symptom_hi = st.text_area("Possible Symptoms (HI)", entry['possible_symptom_hi'] or "")
            first_aid_tips_en = st.text_area("First Aid Tips (EN)", entry['first_aid_tips_en'] or "")
            first_aid_tips_hi = st.text_area("First Aid Tips (HI)", entry['first_aid_tips_hi'] or "")
            prevention_tips_en = st.text_area("Prevention Tips (EN)", entry['prevention_tips_en'] or "")
            prevention_tips_hi = st.text_area("Prevention Tips (HI)", entry['prevention_tips_hi'] or "")
            disclaimer_en = st.text_area("Disclaimer (EN)", entry['disclaimer_en'] or "")
            disclaimer_hi = st.text_area("Disclaimer (HI)", entry['disclaimer_hi'] or "")
            submitted = st.form_submit_button("Save Changes")
            if submitted:
                kb_conn.execute("""
                    UPDATE conditions SET
                        condition_en=?, condition_hi=?, description_en=?, description_hi=?,
                        possible_symptom_en=?, possible_symptom_hi=?, first_aid_tips_en=?, first_aid_tips_hi=?,
                        prevention_tips_en=?, prevention_tips_hi=?, disclaimer_en=?, disclaimer_hi=?
                    WHERE condition_en=?
                """, (
                    condition_en, condition_hi, description_en, description_hi,
                    possible_symptom_en, possible_symptom_hi, first_aid_tips_en, first_aid_tips_hi,
                    prevention_tips_en, prevention_tips_hi, disclaimer_en, disclaimer_hi, selected
                ))
                kb_conn.commit()
                sync_kb_json_from_db(kb_conn)
                update_condition_entities_json(kb_conn)
                st.success("Entry updated!")

        if st.button("Delete Entry"):
            kb_conn.execute("DELETE FROM conditions WHERE condition_en=?", (selected,))
            kb_conn.commit()
            sync_kb_json_from_db(kb_conn)
            update_condition_entities_json(kb_conn)
            st.success("Entry deleted! Please refresh.")

    st.subheader("➕ Add New KB Entry")
    with st.form("add_kb_form"):
        new_condition_en = st.text_input("Condition (EN)")
        new_condition_hi = st.text_input("Condition (HI)")
        new_description_en = st.text_area("Description (EN)")
        new_description_hi = st.text_area("Description (HI)")
        new_possible_symptom_en = st.text_area("Possible Symptoms (EN)")
        new_possible_symptom_hi = st.text_area("Possible Symptoms (HI)")
        new_first_aid_tips_en = st.text_area("First Aid Tips (EN)")
        new_first_aid_tips_hi = st.text_area("First Aid Tips (HI)")
        new_prevention_tips_en = st.text_area("Prevention Tips (EN)")
        new_prevention_tips_hi = st.text_area("Prevention Tips (HI)")
        new_disclaimer_en = st.text_area("Disclaimer (EN)")
        new_disclaimer_hi = st.text_area("Disclaimer (HI)")
        add_submitted = st.form_submit_button("Add Entry")
        if add_submitted and new_condition_en:
            kb_conn.execute("""
                INSERT OR REPLACE INTO conditions (
                    condition_en, condition_hi, description_en, description_hi,
                    possible_symptom_en, possible_symptom_hi, first_aid_tips_en, first_aid_tips_hi,
                    prevention_tips_en, prevention_tips_hi, disclaimer_en, disclaimer_hi
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_condition_en, new_condition_hi, new_description_en, new_description_hi,
                new_possible_symptom_en, new_possible_symptom_hi, new_first_aid_tips_en, new_first_aid_tips_hi,
                new_prevention_tips_en, new_prevention_tips_hi, new_disclaimer_en, new_disclaimer_hi
            ))
            kb_conn.commit()
            sync_kb_json_from_db(kb_conn)
            update_condition_entities_json(kb_conn)
            st.success("New entry added! Please refresh.")

# --- Failed Query Monitoring ---
with st.expander("❓ Failed Queries", expanded=False):
    try:
        fq = pd.read_sql_query("SELECT * FROM failed_queries ORDER BY timestamp DESC", fb_conn)
        st.dataframe(fq)

        st.subheader("Promote a Failed Query to KB")
        fq_selected = st.selectbox("Select a failed query to add to KB", fq['query'].unique())
        if st.button("Promote to KB"):
            st.session_state["new_kb_query"] = fq_selected
            st.success("Go to 'Add New KB Entry' below to complete the entry.")

    except Exception as e:
        st.info("No failed_queries table found yet. It will appear after the first failed query is logged.")

fb_conn.close()
kb_conn.close()