from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from backend.db.connection import get_db
from backend.utils.auth_middleware import get_current_user_id
from backend.utils.helpers import rows_to_dicts, row_to_dict

router = APIRouter(prefix="/api/profile", tags=["profile"])


class ProfileUpdateReq(BaseModel):
    name: Optional[str] = None
    study_goals: Optional[str] = None
    persona: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    accessibility_settings: Optional[str] = None


@router.get("")
def get_profile(user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(
            "SELECT u.id, u.name, u.email, u.email_verified, u.last_login, "
            "p.study_goals, p.persona, p.mood, p.onboarding_complete, "
            "p.avatar_url, p.timezone, p.language, p.accessibility_settings "
            "FROM users u LEFT JOIN profiles p ON u.id=p.user_id WHERE u.id=%s",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "User not found")
        return row_to_dict(cur, row)
    finally:
        cur.close(); conn.close()


@router.put("")
def update_profile(data: ProfileUpdateReq, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        if data.name is not None:
            cur.execute("UPDATE users SET name=%s WHERE id=%s", (data.name.strip(), user_id))

        profile_fields = {}
        if data.study_goals is not None:
            profile_fields["study_goals"] = data.study_goals
        if data.persona is not None:
            profile_fields["persona"] = data.persona
        if data.timezone is not None:
            profile_fields["timezone"] = data.timezone
        if data.language is not None:
            profile_fields["language"] = data.language
        if data.accessibility_settings is not None:
            profile_fields["accessibility_settings"] = data.accessibility_settings

        if profile_fields:
            set_clause = ", ".join(f"{k}=%s" for k in profile_fields.keys())
            values = list(profile_fields.values()) + [user_id]
            cur.execute(f"UPDATE profiles SET {set_clause} WHERE user_id=%s", values)

        conn.commit()
        return {"message": "Profile updated"}
    finally:
        cur.close(); conn.close()


@router.post("/avatar")
async def upload_avatar(file: UploadFile = File(...), user_id: int = Depends(get_current_user_id)):
    import os
    import uuid

    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "avatars")
    os.makedirs(upload_dir, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    if ext not in ["jpg", "jpeg", "png", "gif", "webp"]:
        raise HTTPException(400, "Invalid file type. Use jpg, png, gif, or webp")

    filename = f"{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(upload_dir, filename)

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(400, "File too large. Max 5MB")

    with open(filepath, "wb") as f:
        f.write(content)

    avatar_url = f"/uploads/avatars/{filename}"
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE profiles SET avatar_url=%s WHERE user_id=%s", (avatar_url, user_id))
        conn.commit()
        return {"avatar_url": avatar_url}
    finally:
        cur.close(); conn.close()


@router.get("/activity")
def get_activity(user_id: int = Depends(get_current_user_id), limit: int = 20):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(
            "SELECT activity_type, description, duration_minutes, created_at "
            "FROM activity_logs WHERE user_id=%s ORDER BY created_at DESC LIMIT %s",
            (user_id, limit),
        )
        return rows_to_dicts(cur, cur.fetchall())
    finally:
        cur.close(); conn.close()