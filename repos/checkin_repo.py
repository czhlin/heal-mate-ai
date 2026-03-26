import json

from repos.connection import connect


def save_checkin(user_id: str, check_date: str, completed_tasks_list: list, feedback: str = "", ai_reply: str = ""):
    tasks_json = json.dumps(completed_tasks_list, ensure_ascii=False)
    conn = connect()
    try:
        cur = conn.execute(
            "SELECT id FROM check_ins WHERE user_id = ? AND check_date = ?",
            (user_id, check_date),
        )
        row = cur.fetchone()
        if row:
            conn.execute(
                "UPDATE check_ins SET completed_tasks_json = ?, feedback = ?, ai_reply = ? WHERE id = ?",
                (tasks_json, feedback, ai_reply, row[0]),
            )
        else:
            conn.execute(
                """
                INSERT INTO check_ins (user_id, check_date, completed_tasks_json, feedback, ai_reply) 
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, check_date, tasks_json, feedback, ai_reply),
            )
        conn.commit()
    finally:
        conn.close()


def load_checkin(user_id: str, check_date: str):
    conn = connect()
    try:
        cur = conn.execute(
            "SELECT completed_tasks_json, feedback, ai_reply FROM check_ins WHERE user_id = ? AND check_date = ?",
            (user_id, check_date),
        )
        row = cur.fetchone()
        if row:
            return json.loads(row[0]), row[1], (row[2] if len(row) > 2 else "")
        return [], "", ""
    finally:
        conn.close()


def get_all_checkins(user_id: str):
    conn = connect()
    try:
        cur = conn.execute(
            "SELECT check_date, completed_tasks_json, feedback, ai_reply FROM check_ins WHERE user_id = ? ORDER BY check_date DESC",
            (user_id,),
        )
        rows = cur.fetchall()
        results = []
        for r in rows:
            results.append(
                {
                    "date": r[0],
                    "tasks": json.loads(r[1]),
                    "feedback": r[2] or "",
                    "ai_reply": r[3] or "",
                }
            )
        return results
    finally:
        conn.close()


def get_last_checkin_date(user_id: str):
    conn = connect()
    try:
        cur = conn.execute(
            "SELECT check_date FROM check_ins WHERE user_id = ? ORDER BY check_date DESC LIMIT 1",
            (user_id,),
        )
        row = cur.fetchone()
        if row:
            return row[0]
        return None
    finally:
        conn.close()

