from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.db.connection import get_db
from backend.utils.auth_middleware import get_current_user_id
from backend.utils.helpers import rows_to_dicts

router = APIRouter(prefix="/api/memory", tags=["memory"])


class AddMemoryReq(BaseModel):
    content: str
    category: Optional[str] = "personal_preferences"
    importance: Optional[int] = 2
    pinned: Optional[bool] = False
    is_disabled: Optional[bool] = False


class UpdateMemoryReq(BaseModel):
    content: Optional[str] = None
    category: Optional[str] = None
    importance: Optional[int] = None
    pinned: Optional[bool] = None
    is_disabled: Optional[bool] = None


@router.get("")
def list_memories(category: Optional[str] = None, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        sql = "SELECT id, category, content, importance, pinned, is_disabled, created_at FROM memory_items WHERE user_id=%s"
        params = [user_id]
        if category and category != "all":
            if category == "pinned_memories":
                sql += " AND pinned=1"
            else:
                sql += " AND category=%s"
                params.append(category)
        sql += " ORDER BY pinned DESC, importance DESC, created_at DESC"
        cur.execute(sql, params)
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
            "INSERT INTO memory_items (user_id, category, content, importance, pinned, is_disabled) VALUES (%s,%s,%s,%s,%s,%s)",
            (
                user_id,
                data.category or "personal_preferences",
                content,
                data.importance or 2,
                1 if data.pinned else 0,
                1 if data.is_disabled else 0,
            ),
        )
        conn.commit()
        return {"id": cur.lastrowid, "message": "Memory saved"}
    finally:
        cur.close(); conn.close()


@router.put("/{memory_id}")
def update_memory(memory_id: int, data: UpdateMemoryReq, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        updates, params = [], []
        if data.content is not None:
            updates.append("content=%s"); params.append(data.content.strip())
        if data.category is not None:
            updates.append("category=%s"); params.append(data.category.strip())
        if data.importance is not None:
            updates.append("importance=%s"); params.append(data.importance)
        if data.pinned is not None:
            updates.append("pinned=%s"); params.append(1 if data.pinned else 0)
        if data.is_disabled is not None:
            updates.append("is_disabled=%s"); params.append(1 if data.is_disabled else 0)

        if updates:
            params.extend([memory_id, user_id])
            cur.execute(f"UPDATE memory_items SET {', '.join(updates)} WHERE id=%s AND user_id=%s", params)
            conn.commit()
        return {"message": "Memory updated successfully"}
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
