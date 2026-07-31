from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.db.connection import get_db
from backend.utils.auth_middleware import get_current_user_id
from backend.utils.helpers import rows_to_dicts
from backend.config import PERSONAS

dashboard_router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
settings_router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsReq(BaseModel):
    study_goals: Optional[str] = None
    persona: Optional[str] = None
    mood: Optional[str] = None
    onboarding_complete: Optional[bool] = None


@dashboard_router.get("")
def get_dashboard(user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(
            "SELECT current_streak, longest_streak, total_study_minutes, last_study_date FROM streaks WHERE user_id=%s",
            (user_id,),
        )
        s = cur.fetchone()
        streak = {
            "current_streak": s[0] if s else 0,
            "longest_streak": s[1] if s else 0,
            "total_study_minutes": s[2] if s else 0,
            "last_study_date": (s[3].isoformat() if hasattr(s[3], "isoformat") else str(s[3])) if s and s[3] else None,
        }

        cur.execute(
            "SELECT category, content FROM memory_items WHERE user_id=%s AND category='weak_area' ORDER BY created_at DESC LIMIT 8",
            (user_id,),
        )
        weak_topics = [{"category": r[0], "content": r[1]} for r in cur.fetchall()]

        cur.execute(
            "SELECT qa.score, qa.total, qa.created_at, q.title FROM quiz_attempts qa "
            "JOIN quizzes q ON qa.quiz_id=q.id WHERE qa.user_id=%s ORDER BY qa.created_at DESC LIMIT 10",
            (user_id,),
        )
        quiz_scores = rows_to_dicts(cur, cur.fetchall())

        cur.execute(
            "SELECT activity_type, description, created_at FROM activity_logs WHERE user_id=%s ORDER BY created_at DESC LIMIT 15",
            (user_id,),
        )
        recent_activity = rows_to_dicts(cur, cur.fetchall())

        cur.execute("SELECT COUNT(*) FROM study_materials WHERE user_id=%s", (user_id,))
        notes_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM flashcards WHERE user_id=%s", (user_id,))
        flashcard_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM chat_sessions WHERE user_id=%s", (user_id,))
        chat_count = cur.fetchone()[0]

        cur.execute("SELECT AVG(score*100.0/total) FROM quiz_attempts WHERE user_id=%s AND total>0", (user_id,))
        avg_row = cur.fetchone()
        avg_score = round(float(avg_row[0]), 1) if avg_row and avg_row[0] else 0

        cur.execute("SELECT COUNT(*) FROM quiz_attempts WHERE user_id=%s", (user_id,))
        quiz_count = cur.fetchone()[0]

        return {
            "streak": streak,
            "weak_topics": weak_topics,
            "quiz_scores": quiz_scores,
            "recent_activity": recent_activity,
            "stats": {
                "notes_count": notes_count,
                "flashcard_count": flashcard_count,
                "chat_count": chat_count,
                "quiz_count": quiz_count,
                "avg_quiz_score": avg_score,
            },
        }
    finally:
        cur.close(); conn.close()


@settings_router.get("")
def get_settings(user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(
            "SELECT study_goals, persona, mood, onboarding_complete FROM profiles WHERE user_id=%s",
            (user_id,),
        )
        row = cur.fetchone()
        return {
            "study_goals": row[0] if row else "",
            "persona": row[1] if row else "friendly_buddy",
            "mood": row[2] if row else "neutral",
            "onboarding_complete": bool(row[3]) if row else False,
            "personas": {k: {"name": v["name"], "emoji": v["emoji"]} for k, v in PERSONAS.items()},
        }
    finally:
        cur.close(); conn.close()


@settings_router.put("")
def update_settings(data: SettingsReq, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        if data.study_goals is not None:
            cur.execute("UPDATE profiles SET study_goals=%s WHERE user_id=%s", (data.study_goals, user_id))
        if data.persona and data.persona in PERSONAS:
            cur.execute("UPDATE profiles SET persona=%s WHERE user_id=%s", (data.persona, user_id))
        if data.mood:
            cur.execute("UPDATE profiles SET mood=%s WHERE user_id=%s", (data.mood, user_id))
        if data.onboarding_complete:
            cur.execute("UPDATE profiles SET onboarding_complete=1 WHERE user_id=%s", (user_id,))
        conn.commit()
        return {"message": "Settings updated"}
    finally:
        cur.close(); conn.close()
