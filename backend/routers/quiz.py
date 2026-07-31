import json
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.db.connection import get_db
from backend.utils.auth_middleware import get_current_user_id
from backend.utils.helpers import rows_to_dicts, row_to_dict, parse_json_field, log_activity
from backend.services.ai_service import generate_quiz

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


class GenerateReq(BaseModel):
    material_id: Optional[int] = None
    quiz_type: Optional[str] = "mcq"
    count: Optional[int] = 5
    content: Optional[str] = ""
    title: Optional[str] = "Quiz"


class SubmitReq(BaseModel):
    answers: Dict[str, Any] = {}


@router.get("")
def list_quizzes(user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(
            "SELECT q.id, q.title, q.quiz_type, q.created_at, "
            "(SELECT COUNT(*) FROM quiz_questions WHERE quiz_id=q.id) AS question_count, "
            "(SELECT MAX(score*100/total) FROM quiz_attempts WHERE quiz_id=q.id AND user_id=%s) AS best_score "
            "FROM quizzes q WHERE q.user_id=%s ORDER BY q.created_at DESC",
            (user_id, user_id),
        )
        return rows_to_dicts(cur, cur.fetchall())
    finally:
        cur.close(); conn.close()


@router.post("/generate")
def generate(data: GenerateReq, user_id: int = Depends(get_current_user_id)):
    count = min(int(data.count or 5), 10)
    content = (data.content or "").strip()
    title = (data.title or "Quiz").strip()

    conn = get_db(); cur = conn.cursor()
    try:
        if data.material_id:
            cur.execute("SELECT title, content FROM study_materials WHERE id=%s AND user_id=%s", (data.material_id, user_id))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Material not found")
            title, content = row[0], row[1]
        elif not content:
            cur.execute("SELECT title, content FROM study_materials WHERE user_id=%s ORDER BY created_at DESC LIMIT 1", (user_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(400, "Upload notes first or provide content")
            title, content = row[0], row[1]

        quiz_data = generate_quiz(content, data.quiz_type or "mcq", count)
        final_title = quiz_data.get("title", title)

        cur.execute(
            "INSERT INTO quizzes (user_id, material_id, title, quiz_type) VALUES (%s,%s,%s,%s)",
            (user_id, data.material_id, final_title, data.quiz_type or "mcq"),
        )
        quiz_id = cur.lastrowid

        questions = []
        for q in quiz_data.get("questions", []):
            opts = json.dumps(q.get("options")) if q.get("options") else None
            cur.execute(
                "INSERT INTO quiz_questions (quiz_id, question, options, correct_answer, explanation) VALUES (%s,%s,%s,%s,%s)",
                (quiz_id, q["question"], opts, q["correct_answer"], q.get("explanation", "")),
            )
            questions.append({
                "id": cur.lastrowid, "question": q["question"],
                "options": q.get("options"), "correct_answer": q["correct_answer"],
                "explanation": q.get("explanation", ""),
            })

        log_activity(cur, user_id, "quiz", f"Generated: {final_title}", 5)
        conn.commit()
        return {"id": quiz_id, "title": final_title, "questions": questions}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback(); raise HTTPException(500, str(e))
    finally:
        cur.close(); conn.close()


@router.get("/{quiz_id}")
def get_quiz(quiz_id: int, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, title, quiz_type FROM quizzes WHERE id=%s AND user_id=%s", (quiz_id, user_id))
        quiz = cur.fetchone()
        if not quiz:
            raise HTTPException(404, "Quiz not found")
        cur.execute("SELECT id, question, options, correct_answer, explanation FROM quiz_questions WHERE quiz_id=%s", (quiz_id,))
        questions = []
        for row in cur.fetchall():
            q = row_to_dict(cur, row)
            q["options"] = parse_json_field(q["options"])
            questions.append(q)
        return {"id": quiz[0], "title": quiz[1], "quiz_type": quiz[2], "questions": questions}
    finally:
        cur.close(); conn.close()


@router.post("/{quiz_id}/submit")
def submit(quiz_id: int, data: SubmitReq, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM quizzes WHERE id=%s AND user_id=%s", (quiz_id, user_id))
        if not cur.fetchone():
            raise HTTPException(404, "Quiz not found")

        cur.execute("SELECT id, correct_answer, explanation FROM quiz_questions WHERE quiz_id=%s", (quiz_id,))
        rows = cur.fetchall()
        total = len(rows)
        score = 0
        results = []

        for qid, correct, explanation in rows:
            user_ans = str(data.answers.get(str(qid), "")).strip()
            ok = user_ans.lower() == correct.strip().lower()
            if ok:
                score += 1
            results.append({"question_id": qid, "correct": ok, "correct_answer": correct, "explanation": explanation})

        cur.execute(
            "INSERT INTO quiz_attempts (quiz_id, user_id, score, total, answers) VALUES (%s,%s,%s,%s,%s)",
            (quiz_id, user_id, score, total, json.dumps(data.answers)),
        )
        for r in [x for x in results if not x["correct"]][:3]:
            cur.execute(
                "INSERT INTO memory_items (user_id, category, content, importance) VALUES (%s,'weak_area',%s,2)",
                (user_id, f"Struggled with quiz question #{r['question_id']}"),
            )

        log_activity(cur, user_id, "quiz", f"Scored {score}/{total}", 10)
        conn.commit()
        pct = round(score / total * 100) if total else 0
        return {"score": score, "total": total, "percentage": pct, "results": results}
    finally:
        cur.close(); conn.close()
