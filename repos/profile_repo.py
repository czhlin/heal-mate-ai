from datetime import datetime

from repos.connection import connect


def save_user_profile(user_id: str, user_data: dict):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = connect()
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


def load_latest_user_profile(user_id: str):
    conn = connect()
    try:
        cur = conn.execute(
            """
            SELECT basic_info, goal, diet, allergies, grocery, kitchenware, cooking_time
            FROM users
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,),
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


def clear_user_profiles(user_id: str):
    conn = connect()
    try:
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM plans WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM daily_tasks WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM check_ins WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()

