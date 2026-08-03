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


def _context(cur, user_id, message: str = ""):
    cur.execute("SELECT persona, mood FROM profiles WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    persona = row[0] if row else "friendly_buddy"
    mood = row[1] if row else "neutral"
    cur.execute(
        "SELECT category, content FROM memory_items WHERE user_id=%s ORDER BY importance DESC, created_at DESC LIMIT 5",
        (user_id,),
    )
    memories = [{"category": r[0], "content": r[1]} for r in cur.fetchall()]
    
    notes = ""
    msg_clean = message.lower().strip()
    note_triggers = ["note", "notes", "file", "document", "pdf", "docx", "uploaded", "material", "chapter", "summary", "syllabus", "explain my", "what is in my"]
    if any(trig in msg_clean for trig in note_triggers):
        cur.execute(
            "SELECT content FROM study_materials WHERE user_id=%s ORDER BY created_at DESC LIMIT 2",
            (user_id,),
        )
        notes = "\n\n".join(r[0][:2000] for r in cur.fetchall())
        
    return persona, mood, memories, notes


class SessionUpdateReq(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None
    category: Optional[str] = None


@router.get("/sessions")
def list_sessions(q: Optional[str] = None, category: Optional[str] = None, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        sql = "SELECT id, title, is_pinned, is_favorite, is_archived, category, created_at FROM chat_sessions WHERE user_id=%s"
        params = [user_id]
        if q:
            sql += " AND title LIKE %s"; params.append(f"%{q.strip()}%")
        if category and category != 'all':
            sql += " AND category=%s"; params.append(category)
        sql += " ORDER BY is_pinned DESC, created_at DESC"
        cur.execute(sql, params)
        return rows_to_dicts(cur, cur.fetchall())
    finally:
        cur.close(); conn.close()


@router.post("/sessions")
def create_session(title: Optional[str] = "New Chat", user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO chat_sessions (user_id, title) VALUES (%s,%s)", (user_id, title or "New Chat"))
        conn.commit()
        return {"id": cur.lastrowid, "title": title or "New Chat", "is_pinned": 0, "is_favorite": 0, "is_archived": 0}
    finally:
        cur.close(); conn.close()


@router.put("/sessions/{session_id}")
def update_session(session_id: int, data: SessionUpdateReq, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        updates = []
        params = []
        if data.title is not None:
            updates.append("title=%s"); params.append(data.title.strip())
        if data.is_pinned is not None:
            updates.append("is_pinned=%s"); params.append(1 if data.is_pinned else 0)
        if data.is_favorite is not None:
            updates.append("is_favorite=%s"); params.append(1 if data.is_favorite else 0)
        if data.is_archived is not None:
            updates.append("is_archived=%s"); params.append(1 if data.is_archived else 0)
        if data.category is not None:
            updates.append("category=%s"); params.append(data.category.strip())

        if updates:
            params.extend([session_id, user_id])
            cur.execute(f"UPDATE chat_sessions SET {', '.join(updates)} WHERE id=%s AND user_id=%s", params)
            conn.commit()
        return {"message": "Session updated successfully"}
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


@router.get("/sessions/{session_id}/export")
def export_session(session_id: int, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT title, created_at FROM chat_sessions WHERE id=%s AND user_id=%s", (session_id, user_id))
        session = cur.fetchone()
        if not session:
            raise HTTPException(404, "Session not found")
        cur.execute("SELECT role, content, created_at FROM messages WHERE session_id=%s ORDER BY created_at", (session_id,))
        messages = rows_to_dicts(cur, cur.fetchall())
        markdown_text = f"# Conversation: {session[0]}\n*Exported from Intellix on {session[1]}*\n\n---\n\n"
        for m in messages:
            sender = "👤 User" if m["role"] == "user" else "✨ Intellix"
            markdown_text += f"### {sender}\n{m['content']}\n\n"
        return {"title": session[0], "markdown": markdown_text, "messages": messages}
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


class BatchDeleteReq(BaseModel):
    session_ids: list[int]


@router.post("/sessions/batch-delete")
def batch_delete_sessions(data: BatchDeleteReq, user_id: int = Depends(get_current_user_id)):
    if not data.session_ids:
        return {"message": "No sessions specified"}
    conn = get_db(); cur = conn.cursor()
    try:
        for sid in data.session_ids:
            cur.execute("DELETE FROM chat_sessions WHERE id=%s AND user_id=%s", (sid, user_id))
        conn.commit()
        return {"message": f"Deleted {len(data.session_ids)} sessions"}
    finally:
        cur.close(); conn.close()


class ImportSessionReq(BaseModel):
    title: Optional[str] = "Imported Chat"
    messages: list[dict]


@router.post("/sessions/import")
def import_session(data: ImportSessionReq, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO chat_sessions (user_id, title) VALUES (%s,%s)", (user_id, data.title or "Imported Chat"))
        sid = cur.lastrowid
        for m in data.messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if content:
                cur.execute("INSERT INTO messages (session_id, role, content) VALUES (%s,%s,%s)", (sid, role, content))
        conn.commit()
        return {"id": sid, "title": data.title, "message": "Session imported successfully"}
    finally:
        cur.close(); conn.close()


@router.delete("/sessions")
def clear_all_sessions(user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM chat_sessions WHERE user_id=%s", (user_id,))
        conn.commit()
        return {"message": "All chat sessions deleted"}
    finally:
        cur.close(); conn.close()


@router.get("/sessions/{session_id}/export")
def export_session(session_id: int, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT title FROM chat_sessions WHERE id=%s AND user_id=%s", (session_id, user_id))
        s = cur.fetchone()
        if not s:
            raise HTTPException(404, "Session not found")
        title = s[0] or "Conversation"

        cur.execute("SELECT role, content FROM messages WHERE session_id=%s ORDER BY id ASC", (session_id,))
        rows = cur.fetchall()

        markdown = f"# Nexus AI OS Chat Export: {title}\n"
        markdown += f"*Exported Session #{session_id}*\n\n---\n\n"
        for r, c in rows:
            role_label = "👤 User" if r == "user" else "✨ Nexus AI"
            markdown += f"### {role_label}\n{c}\n\n"

        return {"id": session_id, "title": title, "markdown": markdown}
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

        persona, mood, memories, notes = _context(cur, user_id, message)
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
            persona, mood, memories, notes = _context(cur, user_id, message)
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
