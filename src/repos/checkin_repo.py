import json
import sqlite3
from typing import Optional

from repos.connection import connect


def save_checkin(
    user_id: str,
    check_date: str,
    completed_tasks_list: list,
    feedback: str = "",
    ai_reply: str = "",
    tasks_snapshot_list: Optional[list] = None,
    tasks_total_count: Optional[int] = None,
):
    tasks_json = json.dumps(completed_tasks_list, ensure_ascii=False)
    tasks_snapshot_json = (
        json.dumps(tasks_snapshot_list, ensure_ascii=False) if tasks_snapshot_list is not None else None
    )
    conn = connect()
    try:
        cur = conn.execute(
            "SELECT id FROM check_ins WHERE user_id = ? AND check_date = ?",
            (user_id, check_date),
        )
        row = cur.fetchone()
        if row:
            conn.execute(
                """
                UPDATE check_ins
                SET completed_tasks_json = ?, feedback = ?, ai_reply = ?, tasks_snapshot_json = ?, tasks_total_count = ?
                WHERE id = ?
                """,
                (tasks_json, feedback, ai_reply, tasks_snapshot_json, tasks_total_count, row[0]),
            )
        else:
            conn.execute(
                """
                INSERT INTO check_ins (
                    user_id,
                    check_date,
                    completed_tasks_json,
                    feedback,
                    ai_reply,
                    tasks_snapshot_json,
                    tasks_total_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, check_date, tasks_json, feedback, ai_reply, tasks_snapshot_json, tasks_total_count),
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
        try:
            cur = conn.execute(
                """
                SELECT check_date, completed_tasks_json, feedback, ai_reply, tasks_snapshot_json, tasks_total_count
                FROM check_ins
                WHERE user_id = ?
                ORDER BY check_date DESC
                """,
                (user_id,),
            )
        except sqlite3.OperationalError:
            cur = conn.execute(
                "SELECT check_date, completed_tasks_json, feedback, ai_reply FROM check_ins WHERE user_id = ? ORDER BY check_date DESC",
                (user_id,),
            )
        rows = cur.fetchall()
        results = []
        for r in rows:
            tasks_snapshot = None
            tasks_total = None
            if len(r) >= 6:
                tasks_snapshot = json.loads(r[4]) if r[4] else None
                tasks_total = r[5]
            results.append(
                {
                    "date": r[0],
                    "tasks": json.loads(r[1]),
                    "feedback": r[2] or "",
                    "ai_reply": r[3] or "",
                    "tasks_snapshot": tasks_snapshot,
                    "tasks_total_count": tasks_total,
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
