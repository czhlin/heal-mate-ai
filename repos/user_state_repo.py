from datetime import datetime

from repos.connection import connect


def get_user_state(user_id: str):
    conn = connect()
    try:
        cur = conn.execute(
            "SELECT current_profile_id, current_plan_id, current_tasks_id FROM user_state WHERE user_id = ?",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {"current_profile_id": row[0], "current_plan_id": row[1], "current_tasks_id": row[2]}
    finally:
        conn.close()


def upsert_user_state(user_id: str, current_profile_id=None, current_plan_id=None, current_tasks_id=None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = connect()
    try:
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


def clear_user_state(user_id: str):
    conn = connect()
    try:
        conn.execute("DELETE FROM user_state WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()

