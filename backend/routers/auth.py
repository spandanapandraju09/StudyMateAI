import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
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
def register(data: RegisterRequest):
    name = data.name.strip()
    email = data.email.strip().lower()
    if not name or not email or len(data.password) < 6:
        raise HTTPException(400, "Name, valid email, and password (6+ chars) required")

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            raise HTTPException(409, "Email already registered")

        pw_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
        cur.execute("INSERT INTO users (name, email, password_hash) VALUES (%s,%s,%s)", (name, email, pw_hash))
        uid = cur.lastrowid
        cur.execute("INSERT INTO profiles (user_id) VALUES (%s)", (uid,))
        cur.execute("INSERT INTO streaks (user_id) VALUES (%s)", (uid,))
        conn.commit()
        return {"token": _make_token(uid, email), "user": {"id": uid, "name": name, "email": email, "onboarding_complete": False}}
    finally:
        cur.close(); conn.close()


@router.post("/login")
def login(data: LoginRequest):
    email = data.email.strip().lower()
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT u.id,u.name,u.email,u.password_hash,p.onboarding_complete,p.persona "
            "FROM users u LEFT JOIN profiles p ON u.id=p.user_id WHERE u.email=%s",
            (email,),
        )
        row = cur.fetchone()
        if not row or not bcrypt.checkpw(data.password.encode(), row[3].encode()):
            raise HTTPException(401, "Invalid email or password")
        return {
            "token": _make_token(row[0], row[2]),
            "user": {"id": row[0], "name": row[1], "email": row[2],
                     "onboarding_complete": bool(row[4]), "persona": row[5] or "friendly_buddy"},
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
