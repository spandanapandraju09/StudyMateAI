import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from backend.db.connection import get_db
from backend.config import JWT_SECRET
from backend.utils.auth_middleware import get_current_user_id

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def _make_token(user_id: int, email: str) -> str:
    return jwt.encode(
        {"user_id": user_id, "email": email, "exp": datetime.utcnow() + timedelta(days=7)},
        JWT_SECRET,
        algorithm="HS256",
    )


@router.post("/register")
async def register(data: RegisterRequest, request: Request):
    name = data.name.strip()
    email = data.email.strip().lower()
    if not name or not email or len(data.password) < 6:
        raise HTTPException(400, "Name, valid email, and password (6+ chars) required")

    conn = get_db()
    cur = conn.cursor()
    try:
        # Check if user already exists
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            raise HTTPException(409, "An account with this email already exists")

        # Hash password and create user directly (no OTP needed)
        pw_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
        cur.execute(
            "INSERT INTO users (name, email, password_hash, email_verified) VALUES (%s, %s, %s, 1)",
            (name, email, pw_hash),
        )
        conn.commit()
        uid = cur.lastrowid

        # Create default profile
        cur.execute(
            "INSERT INTO profiles (user_id, persona, mood, onboarding_complete) VALUES (%s, %s, %s, 0)",
            (uid, "friendly_buddy", "neutral"),
        )
        conn.commit()

        token = _make_token(uid, email)
        return {
            "token": token,
            "user": {"id": uid, "name": name, "email": email,
                     "onboarding_complete": False, "persona": "friendly_buddy"},
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, f"Registration failed: {str(e)}")
    finally:
        cur.close(); conn.close()


@router.post("/login")
async def login(data: LoginRequest):
    email = data.email.strip().lower()
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT u.id, u.name, u.email, u.password_hash, u.email_verified, "
            "p.onboarding_complete, p.persona "
            "FROM users u LEFT JOIN profiles p ON u.id=p.user_id WHERE u.email=%s",
            (email,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(401, "Invalid email or password")
        uid, name, email_addr, pw_hash, email_verified, onboarding, persona = row
        # DEBUG: output stored hash and incoming password (remove in prod)
        print('DEBUG login – stored hash:', pw_hash)
        print('DEBUG login – supplied password:', data.password)
        if not bcrypt.checkpw(data.password.encode(), pw_hash.encode()):
            raise HTTPException(401, "Invalid email or password")
        if not email_verified:
            raise HTTPException(403, "Please verify your email before logging in.")
        return {
            "token": _make_token(uid, email_addr),
            "user": {"id": uid, "name": name, "email": email_addr,
                     "onboarding_complete": bool(onboarding), "persona": persona or "friendly_buddy"},
        }
    finally:
        cur.close(); conn.close()


@router.get("/me")
def me(user_id: int = Depends(get_current_user_id)):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT u.id,u.name,u.email,p.study_goals,p.persona,p.mood,p.onboarding_complete "
            "FROM users u JOIN profiles p ON u.id=p.user_id WHERE u.id=%s",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "User not found")
        return {"id": row[0], "name": row[1], "email": row[2], "study_goals": row[3],
                "persona": row[4], "mood": row[5], "onboarding_complete": bool(row[6])}
    finally:
        cur.close(); conn.close()
