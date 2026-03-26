import sqlite3
from datetime import datetime

from config import DB_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS auth (
                user_id TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT 'default',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                basic_info TEXT,
                goal TEXT,
                diet TEXT,
                allergies TEXT,
                grocery TEXT,
                kitchenware TEXT,
                cooking_time TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT 'default',
                created_at TEXT NOT NULL,
                version_key TEXT NOT NULL,
                plan_text TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT 'default',
                created_at TEXT NOT NULL,
                tasks_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS check_ins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT 'default',
                check_date TEXT NOT NULL,
                completed_tasks_json TEXT NOT NULL,
                feedback TEXT,
                UNIQUE(user_id, check_date)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_state (
                user_id TEXT PRIMARY KEY,
                current_profile_id INTEGER,
                current_plan_id INTEGER,
                current_tasks_id INTEGER,
                updated_at TEXT NOT NULL
            )
            """
        )
        try:
            conn.execute("ALTER TABLE users ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default'")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE plans ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default'")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE daily_tasks ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default'")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE check_ins ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default'")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE check_ins ADD COLUMN ai_reply TEXT")
        except sqlite3.OperationalError:
            pass

        try:
            cur = conn.execute("PRAGMA table_info(check_ins)")
            cols = [r[1] for r in cur.fetchall()]
            cur = conn.execute("PRAGMA index_list(check_ins)")
            index_names = [r[1] for r in cur.fetchall() if r[2]]
            has_unique_check_date_only = False
            for idx in index_names:
                cur = conn.execute(f"PRAGMA index_info({idx})")
                idx_cols = [r[2] for r in cur.fetchall()]
                if idx_cols == ["check_date"]:
                    has_unique_check_date_only = True
                    break

            if has_unique_check_date_only:
                conn.execute("ALTER TABLE check_ins RENAME TO check_ins_old")
                conn.execute(
                    """
                    CREATE TABLE check_ins (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL DEFAULT 'default',
                        check_date TEXT NOT NULL,
                        completed_tasks_json TEXT NOT NULL,
                        feedback TEXT,
                        ai_reply TEXT,
                        UNIQUE(user_id, check_date)
                    )
                    """
                )
                if "user_id" in cols:
                    conn.execute(
                        """
                        INSERT INTO check_ins (user_id, check_date, completed_tasks_json, feedback)
                        SELECT user_id, check_date, completed_tasks_json, feedback
                        FROM check_ins_old
                        """
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO check_ins (user_id, check_date, completed_tasks_json, feedback)
                        SELECT 'default', check_date, completed_tasks_json, feedback
                        FROM check_ins_old
                        """
                    )
                conn.execute("DROP TABLE check_ins_old")
        except sqlite3.OperationalError:
            pass

        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_state'")
        if cur.fetchone():
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur = conn.execute(
                """
                SELECT user_id FROM (
                    SELECT user_id FROM users
                    UNION
                    SELECT user_id FROM plans
                    UNION
                    SELECT user_id FROM daily_tasks
                )
                """
            )
            user_ids = [r[0] for r in cur.fetchall() if r and r[0]]
            for user_id in user_ids:
                cur = conn.execute("SELECT id FROM users WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
                row = cur.fetchone()
                current_profile_id = row[0] if row else None

                cur = conn.execute("SELECT id FROM plans WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
                row = cur.fetchone()
                current_plan_id = row[0] if row else None

                cur = conn.execute("SELECT id FROM daily_tasks WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
                row = cur.fetchone()
                current_tasks_id = row[0] if row else None

                if current_profile_id or current_plan_id or current_tasks_id:
                    conn.execute(
                        """
                        INSERT INTO user_state (user_id, current_profile_id, current_plan_id, current_tasks_id, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(user_id) DO UPDATE SET
                            current_profile_id=COALESCE(excluded.current_profile_id, user_state.current_profile_id),
                            current_plan_id=COALESCE(excluded.current_plan_id, user_state.current_plan_id),
                            current_tasks_id=COALESCE(excluded.current_tasks_id, user_state.current_tasks_id),
                            updated_at=excluded.updated_at
                        """,
                        (user_id, current_profile_id, current_plan_id, current_tasks_id, now),
                    )
        conn.commit()
    finally:
        conn.close()
