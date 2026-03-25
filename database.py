import sqlite3
import json
from datetime import datetime
from config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            CREATE TABLE IF NOT EXISTS daily_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                tasks_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS check_ins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_date TEXT NOT NULL UNIQUE,
                completed_tasks_json TEXT NOT NULL,
                feedback TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

def save_user_profile(user_data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            INSERT INTO users (
                created_at, updated_at, basic_info, goal, diet, allergies, grocery, kitchenware, cooking_time
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
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

def load_latest_user_profile():
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            """
            SELECT basic_info, goal, diet, allergies, grocery, kitchenware, cooking_time
            FROM users
            ORDER BY id DESC
            LIMIT 1
            """
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

def clear_user_profiles():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM users")
        conn.execute("DELETE FROM daily_tasks")
        conn.execute("DELETE FROM check_ins")
        conn.commit()
    finally:
        conn.close()

def save_daily_tasks(tasks_list):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tasks_json = json.dumps(tasks_list, ensure_ascii=False)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("INSERT INTO daily_tasks (created_at, tasks_json) VALUES (?, ?)", (now, tasks_json))
        conn.commit()
    finally:
        conn.close()

def load_latest_daily_tasks():
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute("SELECT tasks_json FROM daily_tasks ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            return json.loads(row[0])
        return []
    finally:
        conn.close()

def save_checkin(check_date, completed_tasks_list, feedback=""):
    tasks_json = json.dumps(completed_tasks_list, ensure_ascii=False)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            INSERT INTO check_ins (check_date, completed_tasks_json, feedback) 
            VALUES (?, ?, ?)
            ON CONFLICT(check_date) DO UPDATE SET 
                completed_tasks_json=excluded.completed_tasks_json,
                feedback=excluded.feedback
            """,
            (check_date, tasks_json, feedback)
        )
        conn.commit()
    finally:
        conn.close()

def load_checkin(check_date):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute("SELECT completed_tasks_json, feedback FROM check_ins WHERE check_date = ?", (check_date,))
        row = cur.fetchone()
        if row:
            return json.loads(row[0]), row[1]
        return [], ""
    finally:
        conn.close()

def get_last_checkin_date():
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute("SELECT check_date FROM check_ins ORDER BY check_date DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            return row[0]
        return None
    finally:
        conn.close()
