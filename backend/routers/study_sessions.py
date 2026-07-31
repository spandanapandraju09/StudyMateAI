from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.db.connection import get_db
from backend.utils.auth_middleware import get_current_user_id
from backend.utils.helpers import rows_to_dicts, log_activity, update_streak

router = APIRouter(prefix="/api/study-sessions", tags=["study-sessions"])


class SessionStartReq(BaseModel):
    subject: Optional[str] = None
    material_id: Optional[int] = None


class SessionEndReq(BaseModel):
    session_id: int
    notes: Optional[str] = None


@router.post("/start")
def start_session(data: SessionStartReq, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        start_time = datetime.utcnow().isoformat()
        cur.execute(
            "INSERT INTO study_sessions (user_id, subject, material_id, start_time) VALUES (%s,%s,%s,%s)",
            (user_id, data.subject, data.material_id, start_time),
        )
        session_id = cur.lastrowid
        conn.commit()
        return {"id": session_id, "start_time": start_time, "subject": data.subject}
    finally:
        cur.close(); conn.close()


@router.put("/end")
def end_session(data: SessionEndReq, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT start_time FROM study_sessions WHERE id=%s AND user_id=%s", (data.session_id, user_id))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Session not found")

        start_time = datetime.fromisoformat(row[0])
        end_time = datetime.utcnow()
        duration = int((end_time - start_time).total_seconds() / 60)

        cur.execute(
            "UPDATE study_sessions SET end_time=%s, duration_minutes=%s, notes=%s WHERE id=%s",
            (end_time.isoformat(), duration, data.notes, data.session_id),
        )
        update_streak(cur, user_id, duration)
        log_activity(cur, user_id, "study", f"Studied for {duration} minutes", duration)
        conn.commit()
        return {"message": "Session ended", "duration_minutes": duration}
    finally:
        cur.close(); conn.close()


@router.get("")
def list_sessions(user_id: int = Depends(get_current_user_id), limit: int = 20):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, subject, start_time, end_time, duration_minutes, notes, created_at "
            "FROM study_sessions WHERE user_id=%s ORDER BY start_time DESC LIMIT %s",
            (user_id, limit),
        )
        return rows_to_dicts(cur, cur.fetchall())
    finally:
        cur.close(); conn.close()


@router.get("/stats")
def get_study_stats(user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(
            "SELECT SUM(duration_minutes) as total_minutes, COUNT(*) as session_count, "
            "AVG(duration_minutes) as avg_duration, MAX(duration_minutes) as max_duration "
            "FROM study_sessions WHERE user_id=%s",
            (user_id,),
        )
        row = cur.fetchone()
        stats = {
            "total_minutes": row[0] or 0,
            "session_count": row[1] or 0,
            "avg_duration": round(row[2], 1) if row[2] else 0,
            "max_duration": row[3] or 0,
        }

        cur.execute(
            "SELECT subject, SUM(duration_minutes) as minutes FROM study_sessions "
            "WHERE user_id=%s AND subject IS NOT NULL GROUP BY subject ORDER BY minutes DESC LIMIT 5",
            (user_id,),
        )
        stats["by_subject"] = rows_to_dicts(cur, cur.fetchall())

        return stats
    finally:
        cur.close(); conn.close()