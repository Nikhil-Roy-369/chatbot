import streamlit as st
import httpx

# Backend API (FastAPI in main.py)
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Reset Password", page_icon="🔑", layout="centered")
st.title("🔑 Reset Your Password")

# ✅ Fetch token from reset link
params = st.query_params
token = params.get("token", None)


if not token:
    st.error("❌ Invalid or missing reset link")
else:
    st.info("Please enter your new password below 👇")

    new_pw = st.text_input("🆕 New Password", type="password")
    confirm_pw = st.text_input("✅ Confirm Password", type="password")

    if st.button("💾 Save Password"):
        if not new_pw or not confirm_pw:
            st.warning("⚠️ Both fields are required")
        elif new_pw != confirm_pw:
            st.error("⚠️ Passwords do not match")
        else:
            try:
                res = httpx.post(
                    f"{API_URL}/reset-password",
                    json={"token": token, "new_password": new_pw},
                    timeout=10.0,
                )
                if res.status_code == 200:
                    st.success("✅ Password reset successful! You can now login.")
                else:
                    error_msg = res.json().get("detail", "Something went wrong")
                    st.error(f"❌ Error: {error_msg}")
            except Exception as e:
                st.error(f"🚨 Connection error: {e}")
