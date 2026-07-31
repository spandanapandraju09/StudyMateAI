from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.db.connection import get_db
from backend.utils.auth_middleware import get_current_user_id
from backend.utils.helpers import rows_to_dicts, log_activity
from backend.services.ai_service import generate_flashcards

router = APIRouter(prefix="/api/flashcards", tags=["flashcards"])


class GenerateReq(BaseModel):
    material_id: Optional[int] = None
    count: Optional[int] = 10
    content: Optional[str] = ""


class StatusReq(BaseModel):
    status: str = "new"


@router.get("")
def list_cards(status: Optional[str] = None, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        sql = "SELECT id, front, back, status, review_count, created_at FROM flashcards WHERE user_id=%s"
        params = [user_id]
        if status:
            sql += " AND status=%s"; params.append(status)
        sql += " ORDER BY CASE status WHEN 'unknown' THEN 1 WHEN 'new' THEN 2 WHEN 'known' THEN 3 END, created_at DESC"
        cur.execute(sql, params)
        return rows_to_dicts(cur, cur.fetchall())
    finally:
        cur.close(); conn.close()


@router.post("/generate")
def generate(data: GenerateReq, user_id: int = Depends(get_current_user_id)):
    count = min(int(data.count or 10), 20)
    content = (data.content or "").strip()

    conn = get_db(); cur = conn.cursor()
    try:
        if data.material_id:
            cur.execute("SELECT content FROM study_materials WHERE id=%s AND user_id=%s", (data.material_id, user_id))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Material not found")
            content = row[0]
        elif not content:
            cur.execute("SELECT content FROM study_materials WHERE user_id=%s ORDER BY created_at DESC LIMIT 1", (user_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(400, "Upload notes first or provide content")
            content = row[0]

        card_data = generate_flashcards(content, count)
        cards = []
        for c in card_data.get("cards", []):
            cur.execute(
                "INSERT INTO flashcards (user_id, material_id, front, back) VALUES (%s,%s,%s,%s)",
                (user_id, data.material_id, c["front"], c["back"]),
            )
            cards.append({"id": cur.lastrowid, "front": c["front"], "back": c["back"], "status": "new"})

        log_activity(cur, user_id, "flashcard", f"Generated {len(cards)} flashcards", 5)
        conn.commit()
        return {"cards": cards, "count": len(cards)}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback(); raise HTTPException(500, str(e))
    finally:
        cur.close(); conn.close()


@router.put("/{card_id}/status")
def update_status(card_id: int, data: StatusReq, user_id: int = Depends(get_current_user_id)):
    if data.status not in ("new", "known", "unknown"):
        raise HTTPException(400, "Status must be new, known, or unknown")
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE flashcards SET status=%s, review_count=review_count+1 WHERE id=%s AND user_id=%s",
            (data.status, card_id, user_id),
        )
        if data.status == "unknown":
            cur.execute("SELECT front FROM flashcards WHERE id=%s", (card_id,))
            row = cur.fetchone()
            if row:
                cur.execute(
                    "INSERT INTO memory_items (user_id, category, content, importance) VALUES (%s,'weak_area',%s,2)",
                    (user_id, f"Weak flashcard: {row[0][:80]}"),
                )
        log_activity(cur, user_id, "flashcard", f"Reviewed card #{card_id}", 1)
        conn.commit()
        return {"message": "Updated"}
    finally:
        cur.close(); conn.close()


@router.delete("/{card_id}")
def delete_card(card_id: int, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM flashcards WHERE id=%s AND user_id=%s", (card_id, user_id))
        conn.commit()
        return {"message": "Deleted"}
    finally:
        cur.close(); conn.close()
