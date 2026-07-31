from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.db.connection import get_db
from backend.utils.auth_middleware import get_current_user_id
from backend.utils.helpers import rows_to_dicts

router = APIRouter(prefix="/api/memory", tags=["memory"])


class AddMemoryReq(BaseModel):
    content: str
    category: Optional[str] = "insight"
    importance: Optional[int] = 2


@router.get("")
def list_memories(user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, category, content, importance, created_at FROM memory_items "
            "WHERE user_id=%s ORDER BY importance DESC, created_at DESC",
            (user_id,),
        )
        return rows_to_dicts(cur, cur.fetchall())
    finally:
        cur.close(); conn.close()


@router.post("")
def add_memory(data: AddMemoryReq, user_id: int = Depends(get_current_user_id)):
    content = data.content.strip()
    if not content:
        raise HTTPException(400, "Content required")
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO memory_items (user_id, category, content, importance) VALUES (%s,%s,%s,%s)",
            (user_id, data.category or "insight", content, data.importance or 2),
        )
        conn.commit()
        return {"id": cur.lastrowid, "message": "Memory saved"}
    finally:
        cur.close(); conn.close()


@router.delete("/{memory_id}")
def delete_memory(memory_id: int, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM memory_items WHERE id=%s AND user_id=%s", (memory_id, user_id))
        conn.commit()
        return {"message": "Deleted"}
    finally:
        cur.close(); conn.close()
