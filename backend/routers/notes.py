import os
import re
import io
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from backend.db.connection import get_db
from backend.utils.auth_middleware import get_current_user_id
from backend.utils.helpers import rows_to_dicts, row_to_dict, log_activity

router = APIRouter(prefix="/api/notes", tags=["notes"])
UPLOAD_DIR = os.path.join("/tmp", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Vercel writable temp dir


def _extract(filename: str, data: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(data))
            text = "\n".join(p.extract_text() or "" for p in reader.pages)
            if text.strip():
                return text
        except Exception:
            pass
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(data))
            text = "\n".join(p.extract_text() or "" for p in reader.pages)
            if text.strip():
                return text
        except Exception:
            pass
        raw = data.decode("utf-8", errors="ignore")
        strings = re.findall(r'[\x20-\x7E\s]{5,}', raw)
        clean = "\n".join(s.strip() for s in strings if len(s.strip()) > 5 and not s.strip().startswith("/"))
        return clean or "Extracted PDF content"
    return data.decode("utf-8", errors="ignore")


@router.get("")
def list_notes(user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, title, SUBSTR(content,1,200) AS preview, file_type, created_at "
            "FROM study_materials WHERE user_id=%s ORDER BY created_at DESC",
            (user_id,),
        )
        return rows_to_dicts(cur, cur.fetchall())
    finally:
        cur.close(); conn.close()


@router.get("/{note_id}")
def get_note(note_id: int, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, title, content, file_type, created_at FROM study_materials WHERE id=%s AND user_id=%s",
            (note_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Note not found")
        return row_to_dict(cur, row)
    finally:
        cur.close(); conn.close()


@router.post("")
async def create_note(
    request: Request,
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    user_id: int = Depends(get_current_user_id),
):
    json_data = {}
    if "application/json" in request.headers.get("content-type", ""):
        try:
            json_data = await request.json()
        except Exception:
            json_data = {}

    note_title = (json_data.get("title") or title or "").strip()
    note_content = (json_data.get("content") or content or "").strip()
    file_type = "text"

    if file and file.filename:
        raw = await file.read()
        extracted = _extract(file.filename, raw)
        if extracted.strip():
            note_content = extracted
        note_title = note_title or file.filename
        file_type = file.filename.rsplit(".", 1)[-1].lower()

    if not note_title:
        note_title = "Untitled Notes"
    if not note_content:
        raise HTTPException(400, "Notes content or uploaded file is required")

    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO study_materials (user_id, title, content, file_type) VALUES (%s,%s,%s,%s)",
            (user_id, note_title[:200], note_content, file_type),
        )
        log_activity(cur, user_id, "notes", f"Uploaded: {note_title[:50]}", 5)
        conn.commit()
        return {"id": cur.lastrowid, "title": note_title, "message": "Notes saved successfully"}
    finally:
        cur.close(); conn.close()


@router.delete("/{note_id}")
def delete_note(note_id: int, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM study_materials WHERE id=%s AND user_id=%s", (note_id, user_id))
        conn.commit()
        return {"message": "Deleted"}
    finally:
        cur.close(); conn.close()
