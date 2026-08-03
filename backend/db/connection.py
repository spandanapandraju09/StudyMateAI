import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "study_companion.db")

def _get_schema():
    return """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email_verified INTEGER DEFAULT 0,
    email_verification_token TEXT,
    password_reset_token TEXT,
    password_reset_expires DATETIME,
    last_login DATETIME,
    failed_login_attempts INTEGER DEFAULT 0,
    account_locked INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    study_goals TEXT,
    persona TEXT DEFAULT 'friendly_buddy',
    mood TEXT DEFAULT 'neutral',
    onboarding_complete INTEGER DEFAULT 0,
    avatar_url TEXT,
    timezone TEXT DEFAULT 'UTC',
    language TEXT DEFAULT 'en',
    accessibility_settings TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT DEFAULT 'New Chat',
    pinned INTEGER DEFAULT 0,
    is_pinned INTEGER DEFAULT 0,
    is_favorite INTEGER DEFAULT 0,
    is_archived INTEGER DEFAULT 0,
    category TEXT DEFAULT 'general',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS memory_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category TEXT DEFAULT 'personal_preferences',
    content TEXT NOT NULL,
    importance INTEGER DEFAULT 1,
    pinned INTEGER DEFAULT 0,
    is_disabled INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS study_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    file_type TEXT DEFAULT 'text',
    file_size INTEGER,
    tags TEXT,
    summary TEXT,
    folder TEXT DEFAULT 'documents',
    collection TEXT DEFAULT 'general',
    is_favorite INTEGER DEFAULT 0,
    is_shared INTEGER DEFAULT 0,
    version INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'todo',
    priority TEXT DEFAULT 'medium',
    due_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    frequency TEXT DEFAULT 'daily',
    streak INTEGER DEFAULT 0,
    last_completed TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS sticky_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    color TEXT DEFAULT 'yellow',
    pos_x INTEGER DEFAULT 50,
    pos_y INTEGER DEFAULT 50,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS canvas_boards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content_json TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS prompt_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT NOT NULL,
    prompt_text TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    is_preset INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    material_id INTEGER,
    title TEXT NOT NULL,
    quiz_type TEXT DEFAULT 'mcq',
    difficulty TEXT DEFAULT 'medium',
    time_limit INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS quiz_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    options TEXT,
    correct_answer TEXT NOT NULL,
    explanation TEXT,
    question_type TEXT DEFAULT 'mcq',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    answers TEXT,
    time_taken INTEGER,
    started_at DATETIME,
    completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS flashcards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    material_id INTEGER,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    status TEXT DEFAULT 'new',
    review_count INTEGER DEFAULT 0,
    last_reviewed DATETIME,
    next_review DATETIME,
    ease_factor REAL DEFAULT 2.5,
    interval INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    subject TEXT,
    material_id INTEGER,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    duration_minutes INTEGER DEFAULT 0,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS streaks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_study_date TEXT,
    total_study_minutes INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    achievement_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    xp_reward INTEGER DEFAULT 0,
    unlocked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    goal_type TEXT DEFAULT 'study',
    target_value INTEGER,
    current_value INTEGER DEFAULT 0,
    unit TEXT DEFAULT 'hours',
    deadline DATETIME,
    completed INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    notification_type TEXT DEFAULT 'info',
    read INTEGER DEFAULT 0,
    action_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    theme TEXT DEFAULT 'dark',
    accent_color TEXT DEFAULT '#6C63FF',
    font_size TEXT DEFAULT 'medium',
    notification_enabled INTEGER DEFAULT 1,
    email_notifications INTEGER DEFAULT 1,
    sound_enabled INTEGER DEFAULT 1,
    auto_save INTEGER DEFAULT 1,
    memory_enabled INTEGER DEFAULT 1,
    ai_personality TEXT DEFAULT 'friendly_buddy',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    activity_type TEXT NOT NULL,
    description TEXT,
    duration_minutes INTEGER DEFAULT 0,
    ip_address TEXT,
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    plan_type TEXT DEFAULT 'free',
    status TEXT DEFAULT 'active',
    starts_at DATETIME,
    expires_at DATETIME,
    payment_method TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS admin_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER,
    action TEXT NOT NULL,
    target_user_id INTEGER,
    details TEXT,
    ip_address TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS password_resets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT NOT NULL,
    expires DATETIME NOT NULL,
    used INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS email_verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    otp TEXT NOT NULL,
    expires_at DATETIME NOT NULL,
    attempts INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""


class _Cursor:
    """Wraps sqlite3 cursor to accept %s placeholders and MySQL-style calls."""

    def __init__(self, cur):
        self._c = cur
        self.lastrowid = None
        self.description = None

    def _sql(self, sql):
        s = sql.replace("%s", "?")
        s = s.replace("LEFT(content, 200)", "SUBSTR(content, 1, 200)")
        s = s.replace(
            "FIELD(status, 'unknown', 'new', 'known')",
            "CASE status WHEN 'unknown' THEN 1 WHEN 'new' THEN 2 WHEN 'known' THEN 3 END",
        )
        return s

    def execute(self, sql, params=()):
        self._c.execute(self._sql(sql), params)
        self.lastrowid = self._c.lastrowid
        self.description = self._c.description
        return self

    def executescript(self, sql):
        self._c.executescript(sql)

    def fetchone(self):
        return self._c.fetchone()

    def fetchall(self):
        return self._c.fetchall()

    def close(self):
        self._c.close()


class _Conn:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self, dictionary=False):
        return _Cursor(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def _init(conn):
    conn.cursor().executescript(_get_schema())
    conn.commit()
    # Migration helpers for existing DBs
    cur = conn.cursor()
    cols_to_add = [
        ("chat_sessions", "is_pinned", "INTEGER DEFAULT 0"),
        ("chat_sessions", "is_favorite", "INTEGER DEFAULT 0"),
        ("chat_sessions", "is_archived", "INTEGER DEFAULT 0"),
        ("chat_sessions", "category", "TEXT DEFAULT 'general'"),
        ("memory_items", "pinned", "INTEGER DEFAULT 0"),
        ("memory_items", "is_disabled", "INTEGER DEFAULT 0"),
        ("study_materials", "folder", "TEXT DEFAULT 'documents'"),
        ("study_materials", "collection", "TEXT DEFAULT 'general'"),
        ("study_materials", "is_favorite", "INTEGER DEFAULT 0"),
        ("study_materials", "is_shared", "INTEGER DEFAULT 0"),
        ("study_materials", "version", "INTEGER DEFAULT 1"),
        ("user_settings", "memory_enabled", "INTEGER DEFAULT 1"),
        ("user_settings", "ai_personality", "TEXT DEFAULT 'friendly_buddy'"),
    ]
    for tbl, col, col_def in cols_to_add:
        try:
            cur.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_def}")
            conn.commit()
        except Exception:
            pass
    cur.close()


def get_db():
    db_host = os.getenv("DB_HOST", "localhost")
    db_user = os.getenv("DB_USER", "root")
    db_pass = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "study_companion")

    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=db_host, user=db_user, password=db_pass, database=db_name
        )
        return conn
    except Exception:
        pass

    raw = sqlite3.connect(SQLITE_DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
    raw.execute("PRAGMA journal_mode=WAL")
    raw.execute("PRAGMA foreign_keys=ON")
    wrapped = _Conn(raw)
    _init(wrapped)
    return wrapped
