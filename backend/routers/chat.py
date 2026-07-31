import json
import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.db.connection import get_db
from backend.utils.auth_middleware import get_current_user_id
from backend.utils.helpers import rows_to_dicts, log_activity
from backend.services.ai_service import (
    chat_completion, stream_chat_completion,
    extract_memories, detect_mood, build_system_prompt,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class SendMsg(BaseModel):
    message: str
    session_id: Optional[int] = None


def _context(cur, user_id):
    cur.execute("SELECT persona, mood FROM profiles WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    persona = row[0] if row else "friendly_buddy"
    mood = row[1] if row else "neutral"
    cur.execute(
        "SELECT category, content FROM memory_items WHERE user_id=%s ORDER BY importance DESC, created_at DESC LIMIT 20",
        (user_id,),
    )
    memories = [{"category": r[0], "content": r[1]} for r in cur.fetchall()]
    cur.execute(
        "SELECT content FROM study_materials WHERE user_id=%s ORDER BY created_at DESC LIMIT 3",
        (user_id,),
    )
    notes = "\n\n".join(r[0][:3000] for r in cur.fetchall())
    return persona, mood, memories, notes


@router.get("/sessions")
def list_sessions(user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, title, created_at FROM chat_sessions WHERE user_id=%s ORDER BY created_at DESC",
            (user_id,),
        )
        return rows_to_dicts(cur, cur.fetchall())
    finally:
        cur.close(); conn.close()


@router.post("/sessions")
def create_session(user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO chat_sessions (user_id, title) VALUES (%s,'New Chat')", (user_id,))
        conn.commit()
        return {"id": cur.lastrowid, "title": "New Chat"}
    finally:
        cur.close(); conn.close()


@router.get("/sessions/{session_id}/messages")
def get_messages(session_id: int, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT user_id FROM chat_sessions WHERE id=%s", (session_id,))
        s = cur.fetchone()
        if not s or s[0] != user_id:
            raise HTTPException(404, "Session not found")
        cur.execute(
            "SELECT id, role, content, created_at FROM messages WHERE session_id=%s ORDER BY created_at",
            (session_id,),
        )
        return rows_to_dicts(cur, cur.fetchall())
    finally:
        cur.close(); conn.close()


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM chat_sessions WHERE id=%s AND user_id=%s", (session_id, user_id))
        conn.commit()
        return {"message": "Deleted"}
    finally:
        cur.close(); conn.close()


@router.post("/send")
def send_message(data: SendMsg, user_id: int = Depends(get_current_user_id)):
    message = data.message.strip()
    if not message:
        raise HTTPException(400, "Message required")

    conn = get_db(); cur = conn.cursor()
    try:
        session_id = data.session_id
        if not session_id:
            cur.execute("INSERT INTO chat_sessions (user_id, title) VALUES (%s,%s)", (user_id, message[:60]))
            session_id = cur.lastrowid
        else:
            cur.execute("SELECT user_id FROM chat_sessions WHERE id=%s", (session_id,))
            s = cur.fetchone()
            if not s or s[0] != user_id:
                raise HTTPException(404, "Session not found")

        cur.execute("INSERT INTO messages (session_id, role, content) VALUES (%s,'user',%s)", (session_id, message))
        cur.execute("SELECT role, content FROM messages WHERE session_id=%s ORDER BY created_at", (session_id,))
        history = [{"role": r[0], "content": r[1]} for r in cur.fetchall()]

        persona, mood, memories, notes = _context(cur, user_id)
        detected = detect_mood(message)
        if detected != "neutral":
            mood = detected
            cur.execute("UPDATE profiles SET mood=%s WHERE user_id=%s", (mood, user_id))

        reply = chat_completion(history, persona, mood, memories, notes)
        cur.execute("INSERT INTO messages (session_id, role, content) VALUES (%s,'assistant',%s)", (session_id, reply))

        for mem in extract_memories(message, reply):
            if mem.get("content"):
                cur.execute(
                    "INSERT INTO memory_items (user_id, category, content, importance) VALUES (%s,%s,%s,%s)",
                    (user_id, mem.get("category", "insight"), mem["content"], mem.get("importance", 1)),
                )

        log_activity(cur, user_id, "chat", f"Chat: {message[:60]}", 2)
        conn.commit()
        return {"session_id": session_id, "reply": reply, "mood": mood}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, str(e))
    finally:
        cur.close(); conn.close()


@router.get("/stream")
async def stream_message(
    message: str,
    session_id: Optional[int] = None,
    user_id: int = Depends(get_current_user_id),
):
    async def generator():
        conn = get_db(); cur = conn.cursor()
        try:
            sid = session_id
            if not sid:
                cur.execute("INSERT INTO chat_sessions (user_id, title) VALUES (%s,%s)", (user_id, message[:60]))
                sid = cur.lastrowid
            cur.execute("INSERT INTO messages (session_id, role, content) VALUES (%s,'user',%s)", (sid, message))
            cur.execute("SELECT role, content FROM messages WHERE session_id=%s ORDER BY created_at", (sid,))
            history = [{"role": r[0], "content": r[1]} for r in cur.fetchall()]
            persona, mood, memories, notes = _context(cur, user_id)
            detected = detect_mood(message)
            if detected != "neutral":
                mood = detected
                cur.execute("UPDATE profiles SET mood=%s WHERE user_id=%s", (mood, user_id))
            conn.commit()

            yield f"data: {json.dumps({'session_id': sid, 'mood': mood})}\n\n"

            full_reply = ""
            for chunk in stream_chat_completion(history, persona, mood, memories, notes):
                full_reply += chunk
                yield f"data: {json.dumps({'token': chunk})}\n\n"
                await asyncio.sleep(0)

            conn2 = get_db(); cur2 = conn2.cursor()
            try:
                cur2.execute("INSERT INTO messages (session_id, role, content) VALUES (%s,'assistant',%s)", (sid, full_reply))
                for mem in extract_memories(message, full_reply):
                    if mem.get("content"):
                        cur2.execute(
                            "INSERT INTO memory_items (user_id, category, content, importance) VALUES (%s,%s,%s,%s)",
                            (user_id, mem.get("category", "insight"), mem["content"], mem.get("importance", 1)),
                        )
                log_activity(cur2, user_id, "chat", f"Chat: {message[:60]}", 2)
                conn2.commit()
            finally:
                cur2.close(); conn2.close()

            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            cur.close(); conn.close()

    return StreamingResponse(generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
