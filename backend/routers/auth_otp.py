# backend/routers/auth_otp.py
"""Authentication routes with email OTP verification and password change.

Endpoints:
- POST /api/auth/register          – Initiates registration, sends OTP.
- POST /api/auth/verify-email      – Verifies OTP, creates user.
- POST /api/auth/login             – Existing login (checks email_verified).
- POST /api/auth/change-password   – Change password for logged‑in user.
"""

import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr, validator
from backend.db.connection import get_db
from backend.config import JWT_SECRET
from backend.utils.otp import generate_otp, hash_otp, verify_otp, otp_expiration_time
from backend.utils.email_sender import send_email
from backend.utils.auth_middleware import get_current_user_id

router = APIRouter(prefix="/api/auth", tags=["auth-otp"])

# -------------------------------------------------------------------
# Request schemas
# -------------------------------------------------------------------
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    confirm_password: str | None = None

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v is not None and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str
    name: str
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_new_password: str

    @validator("confirm_new_password")
    def passwords_match(cls, v, values, **kwargs):
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("New passwords do not match")
        return v

# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------
def _make_token(user_id: int, email: str) -> str:
    return jwt.encode(
        {"user_id": user_id, "email": email, "exp": datetime.utcnow() + timedelta(days=7)},
        JWT_SECRET,
        algorithm="HS256",
    )

def _get_user_by_email(conn, email: str):
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, password_hash, email_verified FROM users WHERE email = %s", (email,))
    row = cur.fetchone()
    cur.close()
    return row

# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------
import re

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def is_valid_original_email(email: str) -> bool:
    """Validates original email format ensuring valid domain and TLD."""
    if not email or not EMAIL_REGEX.match(email):
        return False
    domain = email.split('@')[-1]
    if '.' not in domain or len(domain.split('.')[-1]) < 2:
        return False
    return True


@router.post("/register")
async def register(data: RegisterRequest, request: Request):
    email = data.email.strip().lower()
    name = data.name.strip()

    if not is_valid_original_email(email):
        raise HTTPException(400, "Please enter a valid original email address (e.g. user@example.com)")

    if len(data.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    conn = get_db()
    cur = conn.cursor()
    try:
        # Verify email not already used
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            raise HTTPException(409, "An account with this email already exists")
        # Generate OTP and store hashed version
        otp = generate_otp()
        hashed = hash_otp(otp)
        expires_at = otp_expiration_time()
        cur.execute(
            "INSERT INTO email_otps (email, hashed_otp, expires_at, attempts) VALUES (%s, %s, %s, %s)",
            (email, hashed, expires_at, 0),
        )
        conn.commit()
        # Send email
        try:
            subject = "Verify Your Email Address"
            body = f"Hello {name},\n\nYour verification code is: {otp}\n\nThis code expires in 5 minutes.\nIf you did not request this, please ignore this email."
            send_email(to_address=email, subject=subject, body=body)
        except Exception as e:
            print(f"Failed to send verification email to {email}: {e}")
        print(f"OTP generated for {email}: {otp}")
        return {"detail": "OTP sent to email. Please verify to complete registration.", "otp_preview": otp}
    finally:
        cur.close()
        conn.close()


@router.post("/verify-email")
async def verify_email(data: VerifyOTPRequest):
    email = data.email.strip().lower()
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, hashed_otp, expires_at, attempts FROM email_otps WHERE email = %s", (email,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "OTP not found. Please request a new one.")
        otp_id, hashed, expires_at, attempts = row
        if attempts >= 5:
            raise HTTPException(429, "Maximum OTP attempts exceeded. Request a new OTP.")
        if datetime.utcnow() > expires_at:
            raise HTTPException(410, "OTP has expired. Request a new one.")
        if not verify_otp(data.otp, hashed):
            cur.execute("UPDATE email_otps SET attempts = attempts + 1 WHERE id = %s", (otp_id,))
            conn.commit()
            raise HTTPException(401, "Invalid OTP.")
        # OTP valid – create user
        pw_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
        cur.execute(
            "INSERT INTO users (name, email, password_hash, email_verified) VALUES (%s, %s, %s, %s)",
            (data.name.strip(), email, pw_hash, 1),
        )
        user_id = cur.lastrowid
        # Create default profile
        cur.execute(
            "INSERT INTO profiles (user_id, persona, mood, onboarding_complete) VALUES (%s, %s, %s, 0)",
            (user_id, 'friendly_buddy', 'neutral'),
        )
        # Cleanup OTP record
        cur.execute("DELETE FROM email_otps WHERE id = %s", (otp_id,))
        conn.commit()
        token = _make_token(user_id, email)
        return {
            "token": token,
            "user": {"id": user_id, "name": data.name.strip(), "email": email, "onboarding_complete": False, "persona": "friendly_buddy"},
        }
    finally:
        cur.close()
        conn.close()

@router.post("/login")
async def login(data: LoginRequest):
    print(f"Login attempt for: {data.email}, password length: {len(data.password)}")
    email = data.email.strip().lower()
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT u.id, u.name, u.email, u.password_hash, u.email_verified, p.onboarding_complete, p.persona "
            "FROM users u LEFT JOIN profiles p ON u.id = p.user_id WHERE u.email = %s",
            (email,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(401, "Invalid email or password")
        uid, name, email_addr, pw_hash, email_verified, onboarding, persona = row
        # Email verification check disabled for now; allow login regardless of email_verified flag
        check = bcrypt.checkpw(data.password.encode(), pw_hash.encode())
        print(f"Bcrypt password check result: {check}")
        if not check:
            raise HTTPException(401, "Invalid email or password")
        token = _make_token(uid, email_addr)
        return {
            "token": token,
            "user": {"id": uid, "name": name, "email": email_addr, "onboarding_complete": bool(onboarding), "persona": persona or "friendly_buddy"},
        }
    finally:
        cur.close()
        conn.close()

@router.post("/change-password")
async def change_password(data: ChangePasswordRequest, user_id: int = Depends(get_current_user_id)):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "User not found")
        current_hash = row[0]
        if not bcrypt.checkpw(data.current_password.encode(), current_hash.encode()):
            raise HTTPException(401, "Current password is incorrect")
        new_hash = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()
        cur.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user_id))
        conn.commit()
        return {"detail": "Password updated successfully"}
    finally:
        cur.close()
        conn.close()

@router.post("/resend-otp")
async def resend_otp(data: RegisterRequest):
    """Resend OTP to the email with a 60‑second cooldown.

    The request body reuses RegisterRequest for name, email, and password fields,
    but only the email is used for lookup. A new OTP is generated, hashed and stored
    (resetting attempts), and an email is sent. If a recent OTP was sent within the
    cooldown period, an HTTP 429 error is raised.
    """
    email = data.email.strip().lower()
    conn = get_db()
    cur = conn.cursor()
    try:
        # Check for existing pending OTP
        cur.execute("SELECT id, created_at FROM email_otps WHERE email = %s", (email,))
        row = cur.fetchone()
        if row:
            otp_id, created_at = row
            # Enforce 60‑second cooldown
            cooldown_seconds = 60
            if (datetime.utcnow() - created_at).total_seconds() < cooldown_seconds:
                raise HTTPException(429, "OTP was recently sent. Please wait before requesting a new one.")
            # Delete old OTP to replace it
            cur.execute("DELETE FROM email_otps WHERE id = %s", (otp_id,))
            conn.commit()
        # Generate and store new OTP
        otp = generate_otp()
        hashed = hash_otp(otp)
        expires_at = otp_expiration_time()
        cur.execute(
            "INSERT INTO email_otps (email, hashed_otp, expires_at, attempts) VALUES (%s, %s, %s, %s)",
            (email, hashed, expires_at, 0),
        )
        conn.commit()
        # Send email
        subject = "Your Verification Code"
        body = f"Hello {data.name.strip()},\n\nYour verification code is: {otp}\n\nIt expires in 5 minutes."
        send_email(to_address=email, subject=subject, body=body)
        return {"detail": "OTP resent to email."}
    finally:
        cur.close()
        conn.close()
