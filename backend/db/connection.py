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
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_premium INTEGER DEFAULT 0,
    premium_expiry DATETIME NULL
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
    plan_name TEXT NOT NULL,
    payment_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    amount INTEGER NOT NULL,
    currency TEXT NOT NULL,
    payment_status TEXT NOT NULL,
    start_date DATETIME NOT NULL,
    expiry_date DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    payment_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    idempotency_key TEXT UNIQUE,
    amount INTEGER NOT NULL,
    currency TEXT NOT NULL,
    payment_method TEXT,
    status TEXT NOT NULL,
    signature TEXT,
    receipt TEXT,
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
        CREATE TABLE IF NOT EXISTS email_otps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            hashed_otp TEXT NOT NULL,
            expires_at DATETIME NOT NULL,
            attempts INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Movie Ticket Booking Schema & Indexing
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            duration_minutes INTEGER DEFAULT 120,
            release_date TEXT NOT NULL,
            rating REAL DEFAULT 8.0,
            popularity INTEGER DEFAULT 100,
            language TEXT NOT NULL,
            poster_url TEXT,
            trailer_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS genres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS movie_genres (
            movie_id INTEGER NOT NULL,
            genre_id INTEGER NOT NULL,
            PRIMARY KEY (movie_id, genre_id),
            FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
            FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS theaters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            total_seats INTEGER DEFAULT 100,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS showtimes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL,
            theater_id INTEGER NOT NULL,
            show_time DATETIME NOT NULL,
            price REAL NOT NULL,
            screen_name TEXT DEFAULT 'Screen 1',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
            FOREIGN KEY (theater_id) REFERENCES theaters(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS seat_reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            showtime_id INTEGER NOT NULL,
            seat_number TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT DEFAULT 'locked',
            locked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            FOREIGN KEY (showtime_id) REFERENCES showtimes(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS movie_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            showtime_id INTEGER NOT NULL,
            seats_json TEXT NOT NULL,
            total_amount REAL NOT NULL,
            payment_id TEXT,
            idempotency_key TEXT UNIQUE,
            status TEXT DEFAULT 'confirmed',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (showtime_id) REFERENCES showtimes(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS email_delivery_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER,
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            attempts INTEGER DEFAULT 0,
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Performance Indexes preventing full table scans
        CREATE INDEX IF NOT EXISTS idx_movies_language ON movies(language);
        CREATE INDEX IF NOT EXISTS idx_movies_release ON movies(release_date);
        CREATE INDEX IF NOT EXISTS idx_movies_rating ON movies(rating);
        CREATE INDEX IF NOT EXISTS idx_movies_pop ON movies(popularity);
        CREATE INDEX IF NOT EXISTS idx_mg_genre_movie ON movie_genres(genre_id, movie_id);
        CREATE INDEX IF NOT EXISTS idx_mg_movie_genre ON movie_genres(movie_id, genre_id);
        CREATE INDEX IF NOT EXISTS idx_seat_res_lookup ON seat_reservations(showtime_id, seat_number, status);
        CREATE INDEX IF NOT EXISTS idx_seat_res_exp ON seat_reservations(status, expires_at);
        CREATE INDEX IF NOT EXISTS idx_payments_idempotency ON payments(idempotency_key);
        CREATE INDEX IF NOT EXISTS idx_bookings_user ON movie_bookings(user_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_bookings_showtime ON movie_bookings(showtime_id);
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

    def executemany(self, sql, seq_of_params):
        self._c.executemany(self._sql(sql), seq_of_params)
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
    # Ensure email_otps table has no foreign key constraint by dropping any existing version
    cur = conn.cursor()
    try:
        cur.execute('DROP TABLE IF EXISTS email_otps')
        conn.commit()
    except Exception as e:
        print('[INIT] Failed to drop email_otps:', e)
    # Run full schema creation (includes email_otps without FK)
    cur.executescript(_get_schema())
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
        ("users", "email_verified", "INTEGER DEFAULT 0"),
        ("users", "role", "TEXT DEFAULT 'user'"),
        ("payments", "idempotency_key", "TEXT UNIQUE"),
    ]
    for tbl, col, col_def in cols_to_add:
        try:
            cur.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_def}")
            conn.commit()
        except Exception:
            pass

    # Seed Admin User if missing
    cur.execute("SELECT id FROM users WHERE email = 'admin@movietickets.com'")
    admin_row = cur.fetchone()
    if not admin_row:
        import hashlib
        admin_pw_hash = hashlib.sha256("Admin@MovieTickets2026!".encode()).hexdigest()
        cur.execute(
            "INSERT INTO users (name, email, password_hash, email_verified, role) VALUES (%s, %s, %s, 1, 'admin')",
            ("System Admin", "admin@movietickets.com", admin_pw_hash)
        )
        conn.commit()

    # Seed Genres if empty
    cur.execute("SELECT COUNT(*) FROM genres")
    genre_count = cur.fetchone()[0]
    if genre_count == 0:
        default_genres = ["Action", "Comedy", "Drama", "Sci-Fi", "Thriller", "Romance", "Horror", "Animation"]
        for gname in default_genres:
            cur.execute("INSERT INTO genres (name) VALUES (%s)", (gname,))
        conn.commit()

    # Seed Theaters if empty
    cur.execute("SELECT COUNT(*) FROM theaters")
    th_count = cur.fetchone()[0]
    if th_count == 0:
        theaters = [
            ("PVR Superplex", "New York", 100),
            ("IMAX Cinema 3D", "Los Angeles", 120),
            ("Cinepolis Grand", "Chicago", 80),
            ("INOX Leisure", "San Francisco", 90)
        ]
        for tname, city, seats in theaters:
            cur.execute("INSERT INTO theaters (name, city, total_seats) VALUES (%s, %s, %s)", (tname, city, seats))
        conn.commit()

    # Seed Movies if empty
    cur.execute("SELECT COUNT(*) FROM movies")
    mov_count = cur.fetchone()[0]
    if mov_count == 0:
        sample_movies = [
            ("Inception Prime", "A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea.", 148, "2024-07-16", 8.8, 98, "English", "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=500", "https://www.youtube.com/watch?v=YoHD9XEInc0", ["Action", "Sci-Fi", "Thriller"]),
            ("Galactic Odyssey", "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.", 169, "2024-11-07", 8.6, 95, "English", "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=500", "https://www.youtube.com/watch?v=zSWdZVtXT7E", ["Sci-Fi", "Drama"]),
            ("The Dark Knight Saga", "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham.", 152, "2024-07-18", 9.0, 99, "English", "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500", "https://www.youtube.com/watch?v=EXeTwQWrcwY", ["Action", "Thriller"]),
            ("Desi Romance", "A romantic journey across two vibrant cultures with love and comedy.", 135, "2025-02-14", 7.9, 82, "Hindi", "https://images.unsplash.com/photo-1518676590629-3dcbd9c5a5c9?w=500", "https://www.youtube.com/watch?v=YoHD9XEInc0", ["Romance", "Comedy"]),
            ("Vikram - Resurgence", "A high-octane action thriller involving secret agents and underground rings.", 175, "2024-06-03", 8.4, 91, "Tamil", "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500", "https://www.youtube.com/watch?v=zSWdZVtXT7E", ["Action", "Thriller"]),
            ("Kalki 2898 AD", "A modern avatar of Vishnu descends to earth to protect the world from evil forces in a dystopian future.", 180, "2024-06-27", 8.2, 94, "Telugu", "https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?w=500", "https://www.youtube.com/watch?v=EXeTwQWrcwY", ["Action", "Sci-Fi"]),
            ("The Haunted Manor", "A group of investigators encounter supernatural events inside a forgotten mansion.", 110, "2024-10-31", 7.3, 76, "English", "https://images.unsplash.com/photo-1509281373149-e957c6296406?w=500", "https://www.youtube.com/watch?v=YoHD9XEInc0", ["Horror", "Thriller"]),
            ("Cosmic Warriors", "Animated heroes team up to defend the galaxy against alien invasion.", 95, "2025-01-10", 8.0, 88, "Spanish", "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=500", "https://www.youtube.com/watch?v=zSWdZVtXT7E", ["Animation", "Sci-Fi"])
        ]

        cur.execute("SELECT id, name FROM genres")
        gmap = {row[1]: row[0] for row in cur.fetchall()}

        for title, desc, dur, rdate, rating, pop, lang, poster, trailer, gnames in sample_movies:
            cur.execute(
                "INSERT INTO movies (title, description, duration_minutes, release_date, rating, popularity, language, poster_url, trailer_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (title, desc, dur, rdate, rating, pop, lang, poster, trailer)
            )
            mid = cur.lastrowid
            for gname in gnames:
                if gname in gmap:
                    cur.execute("INSERT INTO movie_genres (movie_id, genre_id) VALUES (%s, %s)", (mid, gmap[gname]))

        conn.commit()

    # Seed Showtimes if empty
    cur.execute("SELECT COUNT(*) FROM showtimes")
    st_count = cur.fetchone()[0]
    if st_count == 0:
        import datetime
        now = datetime.datetime.now()
        cur.execute("SELECT id FROM movies")
        m_ids = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT id FROM theaters")
        t_ids = [r[0] for r in cur.fetchall()]

        if m_ids and t_ids:
            for idx, mid in enumerate(m_ids):
                tid = t_ids[idx % len(t_ids)]
                st1 = (now + datetime.timedelta(hours=2 + idx)).strftime("%Y-%m-%d %H:%M:%S")
                st2 = (now + datetime.timedelta(days=1, hours=4 + idx)).strftime("%Y-%m-%d %H:%M:%S")
                cur.execute(
                    "INSERT INTO showtimes (movie_id, theater_id, show_time, price, screen_name) VALUES (%s, %s, %s, %s, %s)",
                    (mid, tid, st1, 14.99, f"Screen {1 + (idx % 3)}")
                )
                cur.execute(
                    "INSERT INTO showtimes (movie_id, theater_id, show_time, price, screen_name) VALUES (%s, %s, %s, %s, %s)",
                    (mid, tid, st2, 17.50, f"Screen {1 + ((idx + 1) % 3)}")
                )
            conn.commit()

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
