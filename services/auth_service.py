import hashlib
import uuid
from datetime import datetime, timedelta

from repos import auth_repo


def verify_or_create_user(user_id: str, password: str) -> bool:
    pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    existing_hash = auth_repo.get_password_hash(user_id)
    if existing_hash:
        return existing_hash == pwd_hash
    auth_repo.create_user(user_id, pwd_hash)
    return True


def create_session(user_id: str, ttl_days: int = 30) -> str:
    now = datetime.now()
    token = uuid.uuid4().hex
    expires_at = now + timedelta(days=ttl_days)
    auth_repo.insert_session(
        token,
        user_id,
        now.strftime("%Y-%m-%d %H:%M:%S"),
        expires_at.strftime("%Y-%m-%d %H:%M:%S"),
    )
    return token


def get_user_id_by_session(token: str):
    row = auth_repo.get_session(token)
    if not row:
        return None
    user_id, expires_at = row["user_id"], row["expires_at"]
    try:
        expires_dt = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        auth_repo.delete_session(token)
        return None
    if expires_dt < datetime.now():
        auth_repo.delete_session(token)
        return None
    return user_id


def delete_session(token: str):
    auth_repo.delete_session(token)

