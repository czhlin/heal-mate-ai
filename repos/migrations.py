import sqlite3

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
        conn.commit()
    finally:
        conn.close()

