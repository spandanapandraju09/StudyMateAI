from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.db.connection import get_db
from backend.utils.auth_middleware import get_current_user_id
from backend.utils.helpers import rows_to_dicts, row_to_dict

router = APIRouter(prefix="/api/workspace", tags=["workspace"])

# --- TASKS ---
class TaskReq(BaseModel):
    title: str
    status: Optional[str] = "todo"
    priority: Optional[str] = "medium"
    due_date: Optional[str] = None

@router.get("/tasks")
def list_tasks(user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, title, status, priority, due_date, created_at FROM tasks WHERE user_id=%s ORDER BY created_at DESC", (user_id,))
        return rows_to_dicts(cur, cur.fetchall())
    finally:
        cur.close(); conn.close()

@router.post("/tasks")
def create_task(data: TaskReq, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO tasks (user_id, title, status, priority, due_date) VALUES (%s,%s,%s,%s,%s)",
                    (user_id, data.title.strip(), data.status or "todo", data.priority or "medium", data.due_date))
        conn.commit()
        return {"id": cur.lastrowid, "title": data.title, "status": data.status or "todo"}
    finally:
        cur.close(); conn.close()

@router.put("/tasks/{task_id}")
def update_task(task_id: int, data: TaskReq, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE tasks SET title=%s, status=%s, priority=%s WHERE id=%s AND user_id=%s",
                    (data.title.strip(), data.status or "todo", data.priority or "medium", task_id, user_id))
        conn.commit()
        return {"message": "Task updated"}
    finally:
        cur.close(); conn.close()

@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM tasks WHERE id=%s AND user_id=%s", (task_id, user_id))
        conn.commit()
        return {"message": "Task deleted"}
    finally:
        cur.close(); conn.close()

# --- HABITS ---
class HabitReq(BaseModel):
    title: str
    frequency: Optional[str] = "daily"

@router.get("/habits")
def list_habits(user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, title, frequency, streak, last_completed, created_at FROM habits WHERE user_id=%s ORDER BY created_at DESC", (user_id,))
        return rows_to_dicts(cur, cur.fetchall())
    finally:
        cur.close(); conn.close()

@router.post("/habits")
def create_habit(data: HabitReq, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO habits (user_id, title, frequency) VALUES (%s,%s,%s)", (user_id, data.title.strip(), data.frequency or "daily"))
        conn.commit()
        return {"id": cur.lastrowid, "title": data.title}
    finally:
        cur.close(); conn.close()

@router.post("/habits/{habit_id}/complete")
def complete_habit(habit_id: int, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE habits SET streak = streak + 1 WHERE id=%s AND user_id=%s", (habit_id, user_id))
        conn.commit()
        return {"message": "Habit streak incremented"}
    finally:
        cur.close(); conn.close()

@router.delete("/habits/{habit_id}")
def delete_habit(habit_id: int, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM habits WHERE id=%s AND user_id=%s", (habit_id, user_id))
        conn.commit()
        return {"message": "Habit deleted"}
    finally:
        cur.close(); conn.close()

# --- STICKY NOTES ---
class StickyNoteReq(BaseModel):
    content: str
    color: Optional[str] = "yellow"
    pos_x: Optional[int] = 50
    pos_y: Optional[int] = 50

@router.get("/sticky-notes")
def list_sticky_notes(user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, content, color, pos_x, pos_y, updated_at FROM sticky_notes WHERE user_id=%s ORDER BY updated_at DESC", (user_id,))
        return rows_to_dicts(cur, cur.fetchall())
    finally:
        cur.close(); conn.close()

@router.post("/sticky-notes")
def create_sticky_note(data: StickyNoteReq, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO sticky_notes (user_id, content, color, pos_x, pos_y) VALUES (%s,%s,%s,%s,%s)",
                    (user_id, data.content.strip(), data.color or "yellow", data.pos_x or 50, data.pos_y or 50))
        conn.commit()
        return {"id": cur.lastrowid, "content": data.content}
    finally:
        cur.close(); conn.close()

@router.delete("/sticky-notes/{note_id}")
def delete_sticky_note(note_id: int, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM sticky_notes WHERE id=%s AND user_id=%s", (note_id, user_id))
        conn.commit()
        return {"message": "Sticky note deleted"}
    finally:
        cur.close(); conn.close()

# --- CANVAS BOARDS ---
class CanvasReq(BaseModel):
    title: str
    content_json: str

@router.get("/canvas")
def list_canvas(user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, title, content_json, created_at, updated_at FROM canvas_boards WHERE user_id=%s ORDER BY updated_at DESC", (user_id,))
        return rows_to_dicts(cur, cur.fetchall())
    finally:
        cur.close(); conn.close()

@router.post("/canvas")
def create_canvas(data: CanvasReq, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO canvas_boards (user_id, title, content_json) VALUES (%s,%s,%s)",
                    (user_id, data.title.strip(), data.content_json))
        conn.commit()
        return {"id": cur.lastrowid, "title": data.title}
    finally:
        cur.close(); conn.close()

# --- PROMPT LIBRARY ---
class PromptTemplateReq(BaseModel):
    title: str
    prompt_text: str
    category: Optional[str] = "coding"

@router.get("/prompts")
def list_prompts(user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, title, prompt_text, category, is_preset, created_at FROM prompt_templates WHERE user_id=%s OR is_preset=1 ORDER BY is_preset DESC, title ASC", (user_id,))
        return rows_to_dicts(cur, cur.fetchall())
    finally:
        cur.close(); conn.close()

@router.post("/prompts")
def create_prompt(data: PromptTemplateReq, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO prompt_templates (user_id, title, prompt_text, category, is_preset) VALUES (%s,%s,%s,%s,0)",
                    (user_id, data.title.strip(), data.prompt_text.strip(), data.category or "coding"))
        conn.commit()
        return {"id": cur.lastrowid, "title": data.title}
    finally:
        cur.close(); conn.close()
