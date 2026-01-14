import sqlite3
from pathlib import Path

DB_NAME = "harmonylink.db"

# script crate table
SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

-------------------------------------------------------
-- 1)  Users
-------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    email          TEXT NOT NULL UNIQUE,
    password_hash  TEXT NOT NULL,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

-------------------------------------------------------
-- 2)   Mood Sessions
-------------------------------------------------------
CREATE TABLE IF NOT EXISTS mood_sessions (
    session_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL,
    stress_level   INTEGER NOT NULL CHECK (stress_level BETWEEN 1 AND 5),
    q1_answer      TEXT,
    q2_answer      TEXT,
    q3_answer      TEXT,
    points_earned  INTEGER NOT NULL DEFAULT 0,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-------------------------------------------------------
-- 3)   Breathing Levels
-------------------------------------------------------
CREATE TABLE IF NOT EXISTS breathing_levels (
    level_id         INTEGER PRIMARY KEY,
    title            TEXT NOT NULL,
    description      TEXT,
    duration_seconds INTEGER NOT NULL,
    base_points      INTEGER NOT NULL
);

INSERT OR IGNORE INTO breathing_levels (level_id, title, description, duration_seconds, base_points)
VALUES
    (1, 'Level 1 - Easy',   'Short and simple breathing exercise.',   60,  10),
    (2, 'Level 2 - Light',  'Slightly longer breathing exercise.',    120, 20),
    (3, 'Level 3 - Medium', 'Moderate breathing exercise.',           180, 30),
    (4, 'Level 4 - Hard',   'Longer and more intense breathing.',     240, 40),
    (5, 'Level 5 - Expert', 'Longest and most challenging exercise.', 300, 50);

-------------------------------------------------------
-- 4)    Breathing Sessions
-------------------------------------------------------
CREATE TABLE IF NOT EXISTS breathing_sessions (
    breathing_session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id              INTEGER NOT NULL,
    session_id           INTEGER,
    level_id             INTEGER NOT NULL,
    started_at           DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at         DATETIME,
    points_earned        INTEGER NOT NULL DEFAULT 0,
    
    FOREIGN KEY (user_id)    REFERENCES users(user_id)             ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES mood_sessions(session_id)  ON DELETE SET NULL,
    FOREIGN KEY (level_id)   REFERENCES breathing_levels(level_id)
);

-------------------------------------------------------
-- 5)   User Stats
-------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_stats (
    user_id             INTEGER PRIMARY KEY,
    total_points        INTEGER NOT NULL DEFAULT 0,
    current_streak_days INTEGER NOT NULL DEFAULT 0,
    last_activity_date  DATE,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
"""


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


# ----------------- CREATE FUNCTIONS ----------------- #

def create_user(name, email, password_hash):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users (name, email, password_hash)
        VALUES (?, ?, ?)
    """, (name, email, password_hash))

    user_id = cur.lastrowid

    cur.execute("INSERT INTO user_stats (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()
    return user_id


def add_mood_session(user_id, stress_level, q1=None, q2=None, q3=None, points_earned=0):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO mood_sessions
            (user_id, stress_level, q1_answer, q2_answer, q3_answer, points_earned)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, stress_level, q1, q2, q3, points_earned))

    sid = cur.lastrowid
    conn.commit()
    conn.close()
    return sid


def add_breathing_session(user_id, level_id, session_id=None, points_earned=0):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO breathing_sessions
            (user_id, session_id, level_id, points_earned)
        VALUES (?, ?, ?, ?)
    """, (user_id, session_id, level_id, points_earned))

    bid = cur.lastrowid
    conn.commit()
    conn.close()
    return bid

# ----------------- update user stats FUNCTIONS ----------------- #

def update_user_stats(user_id, added_points):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE user_stats
        SET
            total_points = total_points + ?,
            current_streak_days =
                CASE
                    WHEN last_activity_date = DATE('now', '-1 day')
                        THEN current_streak_days + 1
                    WHEN last_activity_date = DATE('now')
                        THEN current_streak_days
                    ELSE 1
                END,
            last_activity_date = DATE('now')
        WHERE user_id = ?
    """, (added_points, user_id))

    conn.commit()
    conn.close()


# ----------------- DELETE FUNCTIONS ----------------- #

def delete_user(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    print(f"[✓] User {user_id} deleted successfully.")


def delete_mood_session(session_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM mood_sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

    print(f"[✓] Mood session {session_id} deleted successfully.")


def delete_breathing_session(breathing_session_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM breathing_sessions
        WHERE breathing_session_id = ?
    """, (breathing_session_id,))

    conn.commit()
    conn.close()

    print(f"[✓] Breathing session {breathing_session_id} deleted successfully.")


def delete_breathing_level(level_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM breathing_levels WHERE level_id = ?", (level_id,))
    conn.commit()
    conn.close()

    print(f"[✓] Breathing level {level_id} deleted successfully.")


def delete_user_stats(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM user_stats WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    print(f"[✓] Stats for user {user_id} deleted successfully.")


# ----------------- PRINT FUNCTIONS ----------------- #

def print_users():
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM users").fetchall()
    print("\n===== USERS =====")
    for r in rows:
        print(dict(r))
    conn.close()


def print_mood_sessions():
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM mood_sessions").fetchall()
    print("\n===== MOOD SESSIONS =====")
    for r in rows:
        print(dict(r))
    conn.close()


def print_breathing_levels():
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM breathing_levels").fetchall()
    print("\n===== BREATHING LEVELS =====")
    for r in rows:
        print(dict(r))
    conn.close()


def print_breathing_sessions():
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM breathing_sessions").fetchall()
    print("\n===== BREATHING SESSIONS =====")
    for r in rows:
        print(dict(r))
    conn.close()


def print_user_stats():
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM user_stats").fetchall()
    print("\n===== USER STATS =====")
    for r in rows:
        print(dict(r))
    conn.close()


# ----------------- RUN SCRIPT ----------------- #

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database created successfully!")

    uid = create_user("Moamen User", "moamen@example.com", "hash123")
    sid = add_mood_session(uid, 4, "tired", "not good", "need rest", 5)
    bid = add_breathing_session(uid, 3, sid, 30)
    update_user_stats(uid, 30)

    print_users()
    print_mood_sessions()
    print_breathing_levels()
    print_breathing_sessions()
    print_user_stats()

    # delete_breathing_session(bid)
    # delete_mood_session(sid)
    # delete_user(uid)
