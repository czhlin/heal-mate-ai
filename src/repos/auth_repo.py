from repos.connection import connect


def get_password_hash(user_id: str):
    conn = connect()
    try:
        cur = conn.execute("SELECT password_hash FROM auth WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def create_user(user_id: str, password_hash: str):
    conn = connect()
    try:
        conn.execute("INSERT INTO auth (user_id, password_hash) VALUES (?, ?)", (user_id, password_hash))
        conn.commit()
    finally:
        conn.close()


def insert_session(token: str, user_id: str, created_at: str, expires_at: str):
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO auth_sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, user_id, created_at, expires_at),
        )
        conn.commit()
    finally:
        conn.close()


def get_session(token: str):
    conn = connect()
    try:
        cur = conn.execute(
            "SELECT user_id, expires_at FROM auth_sessions WHERE token = ?",
            (token,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {"user_id": row[0], "expires_at": row[1]}
    finally:
        conn.close()


def delete_session(token: str):
    conn = connect()
    try:
        conn.execute("DELETE FROM auth_sessions WHERE token = ?", (token,))
        conn.commit()
    finally:
        conn.close()
