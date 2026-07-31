from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.db.connection import get_db
from backend.utils.auth_middleware import get_current_user_id
from backend.utils.helpers import rows_to_dicts, log_activity

router = APIRouter(prefix="/api/goals", tags=["goals"])


class GoalReq(BaseModel):
    title: str
    description: Optional[str] = None
    goal_type: str = "study"
    target_value: int
    current_value: int = 0
    unit: str = "hours"
    deadline: Optional[str] = None


class GoalUpdateReq(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_value: Optional[int] = None
    current_value: Optional[int] = None
    deadline: Optional[str] = None
    completed: Optional[bool] = None


@router.get("")
def list_goals(user_id: int = Depends(get_current_user_id), completed: bool = False):
    conn = get_db(); cur = conn.cursor()
    try:
        sql = "SELECT id, title, description, goal_type, target_value, current_value, unit, deadline, completed, created_at FROM goals WHERE user_id=%s"
        params = [user_id]
        if completed:
            sql += " AND completed=1"
        else:
            sql += " AND completed=0"
        sql += " ORDER BY created_at DESC"
        cur.execute(sql, params)
        return rows_to_dicts(cur, cur.fetchall())
    finally:
        cur.close(); conn.close()


@router.post("")
def create_goal(data: GoalReq, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO goals (user_id, title, description, goal_type, target_value, current_value, unit, deadline) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (user_id, data.title, data.description, data.goal_type, data.target_value, data.current_value, data.unit, data.deadline),
        )
        conn.commit()
        log_activity(cur, user_id, "goals", f"Created goal: {data.title[:50]}", 0)
        conn.commit()
        return {"id": cur.lastrowid, "message": "Goal created"}
    finally:
        cur.close(); conn.close()


@router.put("/{goal_id}")
def update_goal(goal_id: int, data: GoalUpdateReq, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM goals WHERE id=%s AND user_id=%s", (goal_id, user_id))
        if not cur.fetchone():
            raise HTTPException(404, "Goal not found")

        updates = {}
        if data.title is not None:
            updates["title"] = data.title
        if data.description is not None:
            updates["description"] = data.description
        if data.target_value is not None:
            updates["target_value"] = data.target_value
        if data.current_value is not None:
            updates["current_value"] = data.current_value
        if data.deadline is not None:
            updates["deadline"] = data.deadline
        if data.completed is not None:
            updates["completed"] = 1 if data.completed else 0

        if updates:
            set_clause = ", ".join(f"{k}=%s" for k in updates.keys())
            values = list(updates.values()) + [goal_id]
            cur.execute(f"UPDATE goals SET {set_clause} WHERE id=%s", values)
            conn.commit()
        return {"message": "Goal updated"}
    finally:
        cur.close(); conn.close()


@router.delete("/{goal_id}")
def delete_goal(goal_id: int, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM goals WHERE id=%s AND user_id=%s", (goal_id, user_id))
        conn.commit()
        return {"message": "Deleted"}
    finally:
        cur.close(); conn.close()