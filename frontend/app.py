import streamlit as st
import httpx
import base64

API_URL = "http://127.0.0.1:8000"

# Session state
if "token" not in st.session_state:  
    st.session_state.token = None
if "email" not in st.session_state:  
    st.session_state.email = None

# ---- API Helpers ----
def api_register(username, email, password, age, location, phone, language):
    return httpx.post(f"{API_URL}/register", json={
        "username": username,
        "email": email,
        "password": password,
        "age": age if age else None,
        "location": location or None,
        "phone": phone or None,
        "language": language or None
    })

def api_login(email_or_username, password):
    r = httpx.post(f"{API_URL}/login", data={
        "username": email_or_username,
        "password": password
    })
    if r.status_code == 200:
        data = r.json()
        st.session_state.token = data["access_token"]
        st.session_state.email = email_or_username
    return r

def api_get_profile():
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    return httpx.get(f"{API_URL}/profile", headers=headers)

def api_update_profile(updates: dict):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    return httpx.put(f"{API_URL}/profile", json=updates, headers=headers)

def logout():
    st.session_state.token = None
    st.session_state.email = None
    st.success("✅ Logged out successfully")

# ---- UI ----
st.set_page_config(page_title="Global Wellness Chatbot", page_icon="🌍", layout="centered")
st.title("🌍 Global Wellness Chatbot")
st.markdown("### 🧘 Stay healthy. Stay connected.")

st.markdown("""
<style>
.stButton button {
  background: linear-gradient(to right, #6a11cb, #2575fc);
  color: white !important;
  border-radius: 8px; padding: 0.6rem 1.2rem; border: none;
  font-weight: bold; width: 100%; margin-bottom: 1rem;
}
.profile-card { background: white; padding: 2rem; border-radius: 15px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.1); text-align: center; width: 60%; margin: auto; }
.avatar { width: 100px; height: 100px; border-radius: 50%; margin-bottom: 1rem; border: 3px solid #2575fc; }
</style>
""", unsafe_allow_html=True)

# ---- Login / Signup / Forgot ----
if not st.session_state.token:
    tab_login, tab_signup, tab_forgot = st.tabs(["🔐 Login", "✨ Signup", "❓ Forgot Password"])

    # ----- LOGIN -----
    with tab_login:
        st.subheader("Login to your account")
        login_id = st.text_input("📧 Email", key="login_id")
        password = st.text_input("🔑 Password", type="password", key="login_password")

        if st.button("✅ Login"):
            if login_id and password:
                res = api_login(login_id, password)
                if res.status_code == 200:
                    st.success("🎉 Login successful!")
                else:
                    try:
                       st.error(f"❌ {res.json().get('detail', 'Invalid credentials')}")
                    except Exception:
                        st.error("❌ Invalid credentials")
            else:
               st.error("⚠️ Please enter your credentials.")

    # ----- SIGNUP -----
    with tab_signup:
        st.subheader("Create a new account")
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("👤 Username", key="signup_username")
            email    = st.text_input("📧 Email", key="signup_email")
            password = st.text_input("🔑 Password", type="password", key="signup_password")
            age      = st.number_input("🎂 Age (optional)", min_value=0, max_value=120, step=1, value=0)
        with col2:
            location = st.text_input("📍 Location (optional)")
            phone    = st.text_input("📱 Phone (optional)")
            language = st.selectbox("🗣️ Preferred Language", ["", "English", "Hindi", "Telugu", "Tamil", "Kannada", "Malayalam", "Bengali", "Marathi", "Gujarati", "Urdu"])

        if st.button("🚀 Register"):
            if username and email and password:
                res = api_register(username, email, password, age if age > 0 else None, location.strip(), phone.strip(), language if language else None)
                if res.status_code == 200:
                    st.success("🎉 User registered! You can now login.")
                else:
                    try:
                        st.error(res.json().get("detail", "Registration failed"))
                    except Exception:
                        st.error("Registration failed")
            else:
                st.error("⚠️ Please fill username, email, and password.")

    # ----- FORGOT PASSWORD -----
    with tab_forgot:
        st.subheader("Forgot Password?")
        forgot_email = st.text_input("📧 Enter your registered email")
        if st.button("📨 Send Reset Link"):
            if forgot_email:
              with st.spinner("Sending reset email..."):
                  try:
                      res = httpx.post(f"{API_URL}/forgot-password", params={"email": forgot_email}, timeout=60)
                      if res.status_code == 200:
                          st.success("✅ Reset link sent! Check your email inbox.")
                      else:
                          st.error(res.json().get("detail", "⚠️ Error sending reset link"))
                  except Exception as e:
                      st.error(f"🚨 Connection error: {e}")
            else:
                st.error("⚠️ Please enter your email")

# ---- Profile (Logged In) ----
else:
    st.markdown("## 👤 User Profile")

    res = api_get_profile()
    if res.status_code != 200:
        st.error("⚠️ Failed to load profile")
    else:
        profile = res.json()

        st.markdown("""
        <style>
        .profile-card { 
            background: none; 
            padding: 2rem; 
            border-radius: 15px; 
            box-shadow: 0 6px 20px rgba(0,0,0,0.05); 
            text-align: center; 
            width: 60%; 
            margin: auto; 
        }
        .avatar { 
            width: 100px; 
            height: 100px; 
            border-radius: 50%; 
            margin-bottom: 1rem; 
            border: 3px solid #2575fc; 
            object-fit: cover;
        }
        .buttons-row { display: flex; justify-content: center; gap: 1rem; margin-top: 1rem; }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("<div class='profile-card'>", unsafe_allow_html=True)

        # Display avatar (no upload)
        avatar_url = profile.get("avatar_url") or "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
        st.markdown(f"<img class='avatar' src='{avatar_url}'>", unsafe_allow_html=True)

        st.markdown(f"### {profile.get('username') or ''} 👋")
        st.markdown(f"📧 **Email:** {profile.get('email') or ''}")

        col1, col2 = st.columns(2)
        with col1:
            new_username = st.text_input("✏️ Update Username", profile.get("username") or "")
            new_location = st.text_input("📍 Update Location", profile.get("location") or "")
            new_language = st.selectbox(
                "🗣️ Preferred Language",
                ["", "English", "Hindi", "Telugu", "Tamil", "Kannada", "Malayalam", "Bengali", "Marathi", "Gujarati", "Urdu"],
                index=(["", "English", "Hindi", "Telugu", "Tamil", "Kannada", "Malayalam", "Bengali", "Marathi", "Gujarati", "Urdu"].index(profile.get("language")) if profile.get("language") else 0)
            )
        with col2:
            new_age = st.number_input("🎂 Update Age", min_value=0, max_value=120, value=int(profile.get("age") or 0), step=1)
            new_phone = st.text_input("📱 Update Phone", profile.get("phone") or "")

        # Buttons in one row
        st.markdown("<div class='buttons-row'>", unsafe_allow_html=True)
        save_clicked = st.button("💾 Save Changes")
        logout_clicked = st.button("🚪 Logout")
        st.markdown("</div>", unsafe_allow_html=True)

        if save_clicked:
            updates = {}
            if new_username != (profile.get("username") or ""): updates["username"] = new_username.strip() or None
            if new_location != (profile.get("location") or ""): updates["location"] = new_location.strip() or None
            if new_language != (profile.get("language") or ""): updates["language"] = new_language or None
            if new_age != int(profile.get("age") or 0): updates["age"] = int(new_age)
            if new_phone != (profile.get("phone") or ""): updates["phone"] = new_phone.strip() or None

            if not updates:
                st.info("No changes to save.")
            else:
                ures = api_update_profile(updates)
                if ures.status_code == 200:
                    st.success("✅ Profile updated successfully! Refreshing…")
                    st.experimental_rerun()
                else:
                    st.error("⚠️ Error updating profile")

        if logout_clicked:
            logout()

        st.markdown("</div>", unsafe_allow_html=True)