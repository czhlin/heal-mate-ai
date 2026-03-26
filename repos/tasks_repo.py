import json
from datetime import datetime

from repos.connection import connect


def save_daily_tasks(user_id: str, tasks_list: list):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tasks_json = json.dumps(tasks_list, ensure_ascii=False)
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO daily_tasks (user_id, created_at, tasks_json) VALUES (?, ?, ?)",
            (user_id, now, tasks_json),
        )
        conn.commit()
    finally:
        conn.close()


def load_latest_daily_tasks(user_id: str):
    conn = connect()
    try:
        cur = conn.execute(
            "SELECT tasks_json FROM daily_tasks WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        )
        row = cur.fetchone()
        if row:
            return json.loads(row[0])
        return []
    finally:
        conn.close()

