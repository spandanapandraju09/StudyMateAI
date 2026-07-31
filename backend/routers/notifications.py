from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.db.connection import get_db
from backend.utils.auth_middleware import get_current_user_id
from backend.utils.helpers import rows_to_dicts, log_activity

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationSettingsReq(BaseModel):
    notification_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    sound_enabled: Optional[bool] = None


@router.get("")
def list_notifications(user_id: int = Depends(get_current_user_id), unread_only: bool = False):
    conn = get_db(); cur = conn.cursor()
    try:
        sql = "SELECT id, title, message, notification_type, read, action_url, created_at FROM notifications WHERE user_id=%s"
        params = [user_id]
        if unread_only:
            sql += " AND read=0"
        sql += " ORDER BY created_at DESC LIMIT 50"
        cur.execute(sql, params)
        return rows_to_dicts(cur, cur.fetchall())
    finally:
        cur.close(); conn.close()


@router.put("/{notification_id}/read")
def mark_read(notification_id: int, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE notifications SET read=1 WHERE id=%s AND user_id=%s", (notification_id, user_id))
        conn.commit()
        return {"message": "Marked as read"}
    finally:
        cur.close(); conn.close()


@router.put("/read-all")
def mark_all_read(user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE notifications SET read=1 WHERE user_id=%s AND read=0", (user_id,))
        conn.commit()
        return {"message": "All notifications marked as read"}
    finally:
        cur.close(); conn.close()


@router.get("/settings")
def get_notification_settings(user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT notification_enabled, email_notifications, sound_enabled FROM user_settings WHERE user_id=%s", (user_id,))
        row = cur.fetchone()
        if not row:
            return {"notification_enabled": True, "email_notifications": True, "sound_enabled": True}
        return {"notification_enabled": bool(row[0]), "email_notifications": bool(row[1]), "sound_enabled": bool(row[2])}
    finally:
        cur.close(); conn.close()


@router.put("/settings")
def update_notification_settings(data: NotificationSettingsReq, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        if data.notification_enabled is not None:
            cur.execute("UPDATE user_settings SET notification_enabled=%s WHERE user_id=%s", (1 if data.notification_enabled else 0, user_id))
        if data.email_notifications is not None:
            cur.execute("UPDATE user_settings SET email_notifications=%s WHERE user_id=%s", (1 if data.email_notifications else 0, user_id))
        if data.sound_enabled is not None:
            cur.execute("UPDATE user_settings SET sound_enabled=%s WHERE user_id=%s", (1 if data.sound_enabled else 0, user_id))
        conn.commit()
        return {"message": "Settings updated"}
    finally:
        cur.close(); conn.close()


@router.delete("/{notification_id}")
def delete_notification(notification_id: int, user_id: int = Depends(get_current_user_id)):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM notifications WHERE id=%s AND user_id=%s", (notification_id, user_id))
        conn.commit()
        return {"message": "Deleted"}
    finally:
        cur.close(); conn.close()