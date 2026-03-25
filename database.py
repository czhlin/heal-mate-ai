import sqlite3
import json
import hashlib
import uuid
from datetime import datetime, timedelta
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

def verify_or_create_user(user_id, password):
    pwd_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute("SELECT password_hash FROM auth WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row:
            return row[0] == pwd_hash
        else:
            conn.execute("INSERT INTO auth (user_id, password_hash) VALUES (?, ?)", (user_id, pwd_hash))
            conn.commit()
            return True
    finally:
        conn.close()

def create_session(user_id, ttl_days=30):
    now = datetime.now()
    token = uuid.uuid4().hex
    expires_at = now + timedelta(days=ttl_days)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO auth_sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (
                token,
                user_id,
                now.strftime("%Y-%m-%d %H:%M:%S"),
                expires_at.strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()
        return token
    finally:
        conn.close()

def get_user_id_by_session(token):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            "SELECT user_id, expires_at FROM auth_sessions WHERE token = ?",
            (token,),
        )
        row = cur.fetchone()
        if not row:
            return None
        user_id, expires_at = row[0], row[1]
        try:
            expires_dt = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            conn.execute("DELETE FROM auth_sessions WHERE token = ?", (token,))
            conn.commit()
            return None
        if expires_dt < datetime.now():
            conn.execute("DELETE FROM auth_sessions WHERE token = ?", (token,))
            conn.commit()
            return None
        return user_id
    finally:
        conn.close()

def delete_session(token):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM auth_sessions WHERE token = ?", (token,))
        conn.commit()
    finally:
        conn.close()

def save_user_profile(user_id, user_data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            INSERT INTO users (
                user_id, created_at, updated_at, basic_info, goal, diet, allergies, grocery, kitchenware, cooking_time
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                now,
                now,
                user_data.get("basic_info"),
                user_data.get("goal"),
                user_data.get("diet"),
                user_data.get("allergies"),
                user_data.get("grocery"),
                user_data.get("kitchenware"),
                user_data.get("cooking_time"),
            ),
        )
        conn.commit()
    finally:
        conn.close()

def load_latest_user_profile(user_id):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            """
            SELECT basic_info, goal, diet, allergies, grocery, kitchenware, cooking_time
            FROM users
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "basic_info": row[0] or "",
            "goal": row[1] or "",
            "diet": row[2] or "",
            "allergies": row[3] or "",
            "grocery": row[4] or "",
            "kitchenware": row[5] or "",
            "cooking_time": row[6] or "",
        }
    finally:
        conn.close()

def clear_user_profiles(user_id):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM plans WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM daily_tasks WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM check_ins WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()

def save_daily_tasks(user_id, tasks_list):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tasks_json = json.dumps(tasks_list, ensure_ascii=False)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("INSERT INTO daily_tasks (user_id, created_at, tasks_json) VALUES (?, ?, ?)", (user_id, now, tasks_json))
        conn.commit()
    finally:
        conn.close()

def load_latest_daily_tasks(user_id):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute("SELECT tasks_json FROM daily_tasks WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
        row = cur.fetchone()
        if row:
            return json.loads(row[0])
        return []
    finally:
        conn.close()

def save_checkin(user_id, check_date, completed_tasks_list, feedback=""):
    tasks_json = json.dumps(completed_tasks_list, ensure_ascii=False)
    conn = sqlite3.connect(DB_PATH)
    try:
        # 由于旧表的 check_date 可能是唯一的，这里更新一下逻辑：先查询是否存在，存在则 UPDATE，否则 INSERT
        cur = conn.execute("SELECT id FROM check_ins WHERE user_id = ? AND check_date = ?", (user_id, check_date))
        row = cur.fetchone()
        if row:
            conn.execute(
                "UPDATE check_ins SET completed_tasks_json = ?, feedback = ? WHERE id = ?",
                (tasks_json, feedback, row[0])
            )
        else:
            conn.execute(
                """
                INSERT INTO check_ins (user_id, check_date, completed_tasks_json, feedback) 
                VALUES (?, ?, ?, ?)
                """,
                (user_id, check_date, tasks_json, feedback)
            )
        conn.commit()
    finally:
        conn.close()

def load_checkin(user_id, check_date):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute("SELECT completed_tasks_json, feedback FROM check_ins WHERE user_id = ? AND check_date = ?", (user_id, check_date))
        row = cur.fetchone()
        if row:
            return json.loads(row[0]), row[1]
        return [], ""
    finally:
        conn.close()

def get_last_checkin_date(user_id):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute("SELECT check_date FROM check_ins WHERE user_id = ? ORDER BY check_date DESC LIMIT 1", (user_id,))
        row = cur.fetchone()
        if row:
            return row[0]
        return None
    finally:
        conn.close()

def save_plan(user_id, version_key, plan_text):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO plans (user_id, created_at, version_key, plan_text) VALUES (?, ?, ?, ?)",
            (user_id, now, version_key, plan_text),
        )
        conn.commit()
    finally:
        conn.close()

def load_latest_plan(user_id):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            "SELECT created_at, version_key, plan_text FROM plans WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return {"created_at": row[0], "version_key": row[1], "plan_text": row[2]}
    finally:
        conn.close()
