from datetime import datetime

from repos.connection import connect


def save_plan(user_id: str, version_key: str, plan_text: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = connect()
    try:
        cur = conn.execute(
            "INSERT INTO plans (user_id, created_at, version_key, plan_text) VALUES (?, ?, ?, ?)",
            (user_id, now, version_key, plan_text),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def load_latest_plan(user_id: str):
    conn = connect()
    try:
        cur = conn.execute(
            "SELECT created_at, version_key, plan_text FROM plans WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {"created_at": row[0], "version_key": row[1], "plan_text": row[2]}
    finally:
        conn.close()


def load_plan_by_id(plan_id: int):
    conn = connect()
    try:
        cur = conn.execute(
            "SELECT created_at, version_key, plan_text FROM plans WHERE id = ? LIMIT 1",
            (plan_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {"created_at": row[0], "version_key": row[1], "plan_text": row[2]}
    finally:
        conn.close()
