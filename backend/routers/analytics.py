from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from backend.db.connection import get_db
from backend.utils.auth_middleware import get_current_user_id
from backend.utils.helpers import rows_to_dicts

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview")
def get_analytics_overview(user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        # Study time stats
        cur.execute(
            "SELECT SUM(duration_minutes) as total_minutes, COUNT(*) as session_count, "
            "AVG(duration_minutes) as avg_duration FROM study_sessions WHERE user_id=%s",
            (user_id,),
        )
        study_stats = cur.fetchone()
        study_data = {
            "total_minutes": study_stats[0] or 0,
            "session_count": study_stats[1] or 0,
            "avg_duration": round(study_stats[2], 1) if study_stats[2] else 0,
        }

        # Quiz performance
        cur.execute(
            "SELECT AVG(score*100.0/total) as avg_score, COUNT(*) as quiz_count, "
            "MAX(score*100.0/total) as best_score FROM quiz_attempts WHERE user_id=%s AND total>0",
            (user_id,),
        )
        quiz_stats = cur.fetchone()
        quiz_data = {
            "avg_score": round(quiz_stats[0], 1) if quiz_stats[0] else 0,
            "quiz_count": quiz_stats[1] or 0,
            "best_score": round(quiz_stats[2], 1) if quiz_stats[2] else 0,
        }

        # Flashcard stats
        cur.execute(
            "SELECT status, COUNT(*) as count FROM flashcards WHERE user_id=%s GROUP BY status",
            (user_id,),
        )
        flashcard_stats = rows_to_dicts(cur, cur.fetchall())

        # Notes count
        cur.execute("SELECT COUNT(*) FROM study_materials WHERE user_id=%s", (user_id,))
        notes_count = cur.fetchone()[0]

        # Chat count
        cur.execute("SELECT COUNT(*) FROM chat_sessions WHERE user_id=%s", (user_id,))
        chat_count = cur.fetchone()[0]

        # Weak areas
        cur.execute(
            "SELECT content, COUNT(*) as count FROM memory_items "
            "WHERE user_id=%s AND category='weak_area' GROUP BY content ORDER BY count DESC LIMIT 5",
            (user_id,),
        )
        weak_areas = rows_to_dicts(cur, cur.fetchall())

        # Recent activity (last 7 days)
        cur.execute(
            "SELECT DATE(created_at) as date, COUNT(*) as count, SUM(duration_minutes) as minutes "
            "FROM activity_logs WHERE user_id=%s AND created_at >= datetime('now', '-7 days') "
            "GROUP BY DATE(created_at) ORDER BY date DESC",
            (user_id,),
        )
        recent_activity = rows_to_dicts(cur, cur.fetchall())

        return {
            "study": study_data,
            "quiz": quiz_data,
            "flashcards": flashcard_stats,
            "notes_count": notes_count,
            "chat_count": chat_count,
            "weak_areas": weak_areas,
            "recent_activity": recent_activity,
        }
    finally:
        cur.close(); conn.close()


@router.get("/study-time")
def get_study_time_analytics(user_id: int = Depends(get_current_user_id), days: int = 30):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(
            "SELECT DATE(start_time) as date, SUM(duration_minutes) as minutes, COUNT(*) as sessions "
            "FROM study_sessions WHERE user_id=%s AND start_time >= datetime('now', '-%d days') "
            "GROUP BY DATE(start_time) ORDER BY date ASC",
            (user_id, days),
        )
        return rows_to_dicts(cur, cur.fetchall())
    finally:
        cur.close(); conn.close()


@router.get("/quiz-performance")
def get_quiz_performance(user_id: int = Depends(get_current_user_id), limit: int = 20):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(
            "SELECT qa.score, qa.total, qa.created_at, q.title, q.quiz_type "
            "FROM quiz_attempts qa JOIN quizzes q ON qa.quiz_id=q.id "
            "WHERE qa.user_id=%s ORDER BY qa.created_at DESC LIMIT %s",
            (user_id, limit),
        )
        results = rows_to_dicts(cur, cur.fetchall())
        for r in results:
            r["percentage"] = round(r["score"] / r["total"] * 100) if r["total"] > 0 else 0
        return results
    finally:
        cur.close(); conn.close()


@router.get("/weak-areas")
def get_weak_areas(user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(
            "SELECT content, category, importance, created_at FROM memory_items "
            "WHERE user_id=%s AND category='weak_area' ORDER BY importance DESC, created_at DESC LIMIT 20",
            (user_id,),
        )
        return rows_to_dicts(cur, cur.fetchall())
    finally:
        cur.close(); conn.close()


@router.get("/progress-prediction")
def get_progress_prediction(user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        # Calculate study streak
        cur.execute("SELECT current_streak, longest_streak, total_study_minutes FROM streaks WHERE user_id=%s", (user_id,))
        streak_row = cur.fetchone()
        streak_data = {
            "current_streak": streak_row[0] if streak_row else 0,
            "longest_streak": streak_row[1] if streak_row else 0,
            "total_study_minutes": streak_row[2] if streak_row else 0,
        }

        # Calculate average quiz score trend
        cur.execute(
            "SELECT score, total, created_at FROM quiz_attempts "
            "WHERE user_id=%s ORDER BY created_at ASC LIMIT 10",
            (user_id,),
        )
        quiz_rows = cur.fetchall()
        quiz_trend = []
        for score, total, created_at in quiz_rows:
            quiz_trend.append({
                "percentage": round(score / total * 100) if total > 0 else 0,
                "date": created_at,
            })

        # Simple prediction based on recent performance
        if len(quiz_trend) >= 3:
            recent_avg = sum(q["percentage"] for q in quiz_trend[-3:]) / 3
            prediction = min(100, recent_avg + 5)  # Assume 5% improvement
        else:
            prediction = 75  # Default prediction

        return {
            "streak": streak_data,
            "quiz_trend": quiz_trend,
            "predicted_score": round(prediction, 1),
            "recommendation": "Keep up the consistent study routine! You're on track for improvement.",
        }
    finally:
        cur.close(); conn.close()