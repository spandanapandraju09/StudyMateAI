import json
from datetime import date, timedelta


def row_to_dict(cursor, row):
    if row is None:
        return None
    cols = [c[0] for c in cursor.description]
    result = dict(zip(cols, row))
    for k, v in result.items():
        if hasattr(v, "isoformat"):
            result[k] = v.isoformat()
    return result


def rows_to_dicts(cursor, rows):
    return [row_to_dict(cursor, r) for r in rows]


def parse_json_field(value):
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return value


def update_streak(cursor, user_id: int, minutes: int = 0):
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    cursor.execute(
        "SELECT current_streak, longest_streak, last_study_date, total_study_minutes FROM streaks WHERE user_id = %s",
        (user_id,),
    )
    row = cursor.fetchone()
    if not row:
        cursor.execute(
            "INSERT INTO streaks (user_id, current_streak, longest_streak, last_study_date, total_study_minutes) VALUES (%s,1,1,%s,%s)",
            (user_id, today, minutes),
        )
        return

    current, longest, last_date, total = row
    total = (total or 0) + minutes
    last_str = last_date.isoformat() if hasattr(last_date, "isoformat") else str(last_date or "")

    if last_str == today:
        new_current = current
    elif last_str == yesterday:
        new_current = (current or 0) + 1
    else:
        new_current = 1

    new_longest = max(longest or 0, new_current)
    cursor.execute(
        "UPDATE streaks SET current_streak=%s, longest_streak=%s, last_study_date=%s, total_study_minutes=%s WHERE user_id=%s",
        (new_current, new_longest, today, total, user_id),
    )


def log_activity(cursor, user_id: int, activity_type: str, description: str = "", minutes: int = 0):
    cursor.execute(
        "INSERT INTO activity_logs (user_id, activity_type, description, duration_minutes) VALUES (%s,%s,%s,%s)",
        (user_id, activity_type, description, minutes),
    )
    update_streak(cursor, user_id, minutes)
