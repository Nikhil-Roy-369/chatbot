import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from dotenv import load_dotenv
from pathlib import Path
import smtplib
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ---------- Import DB functions ----------
from .database import get_db, init_db, row_to_dict, get_user_by_email_or_username

# ---------- Load .env ----------
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
SMTP_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("EMAIL_PORT", 587))
SMTP_USER = os.getenv("EMAIL_USER")
SMTP_PASS = os.getenv("EMAIL_PASS")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")

print("SMTP_USER:", SMTP_USER)
print("SMTP_PASS:", SMTP_PASS)

# ---------- Config ----------
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
RESET_TOKEN_EXPIRE_MINUTES = 15
FRONTEND_URL = "http://localhost:8501"   # Streamlit frontend

app = FastAPI(title="Global Wellness Backend")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ---------- Initialize DB ----------
init_db()

# ---------- Schemas ----------
class RegisterUser(BaseModel):
    username: str
    email: str
    password: str
    age: Optional[int] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    language: Optional[str] = None

class UpdateProfile(BaseModel):
    username: Optional[str] = None
    age: Optional[int] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    language: Optional[str] = None

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

# ---------- Utils ----------
def get_password_hash(pw: str) -> str:
    return pwd_context.hash(pw)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=minutes)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=401, detail="User not found")
    return row_to_dict(row)

def send_reset_email(to_email: str, token: str):
    reset_link = f"{FRONTEND_URL}/reset_password?token={token}"
    subject = "Password Reset Request"
    body = f"""
    Hi,

    We received a request to reset your password.
    Click the link below to reset it:

    {reset_link}

    If you didn’t request this, you can ignore this email.

    Best,
    Global Wellness Team
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())

        print(f"✅ Reset email sent to {to_email}")
        print(f"🔗 Reset link (debug): {reset_link}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# ---------- Endpoints ----------
@app.post("/register")
def register(user: RegisterUser):
    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO users (username, password, email, age, location, phone, language)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user.username,
                get_password_hash(user.password),
                user.email,
                user.age,
                user.location,
                user.phone,
                user.language
            )
        )
        conn.commit()
        return {"message": "User registered successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")
    finally:
        conn.close()

@app.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_email_or_username(form.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username/email or password")

    if not verify_password(form.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username/email or password")

    token = create_access_token({"sub": user["email"]})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/profile")
def get_profile(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "email": current_user["email"],
        "age": current_user.get("age"),
        "location": current_user.get("location"),
        "phone": current_user.get("phone"),
        "language": current_user.get("language"),
    }

@app.put("/profile")
def update_profile(payload: UpdateProfile, current_user: dict = Depends(get_current_user)):
    fields, values = [], []
    for name in ["username", "age", "location", "phone", "language"]:
        val = getattr(payload, name)
        if val is not None:
            fields.append(f"{name} = ?")
            values.append(val)

    if not fields:
        return {"message": "Nothing to update"}

    values.append(current_user["email"])
    conn = get_db()
    conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE email = ?", values)
    conn.commit()
    conn.close()
    return {"message": "Profile updated successfully"}

@app.post("/forgot-password")
def forgot_password(email: str = Query(...)):
    user = get_user_by_email_or_username(email)
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    reset_token = create_access_token({"sub": user["email"]}, minutes=RESET_TOKEN_EXPIRE_MINUTES)
    send_reset_email(user["email"], reset_token)
    return {"message": "Password reset email sent"}

@app.post("/reset-password")
def reset_password(payload: ResetPasswordRequest):
    try:
        data = jwt.decode(payload.token, SECRET_KEY, algorithms=[ALGORITHM])
        email = data.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    hashed_pw = get_password_hash(payload.new_password)
    conn = get_db()
    conn.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_pw, email))
    conn.commit()
    conn.close()
    return {"message": "Password reset successful"}
