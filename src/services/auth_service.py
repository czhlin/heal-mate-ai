"""
服务层 (Service Layer): 身份与会话管理服务

本模块封装了身份验证、自动注册及会话令牌 (Session Token) 的生成与验证。
作为业务逻辑的承载者，它向下调用 Repository 层与数据库交互，向上为 View 层或 App 入口提供干净的鉴权接口。
这种设计有效隔离了加密算法 (SHA-256)、会话过期逻辑与底层的数据存取。
"""

import hashlib
import uuid
from datetime import datetime, timedelta

from repos import auth_repo


def verify_or_create_user(user_id: str, password: str) -> bool:
    """
    登录与隐式注册合一的业务逻辑 (Implicit Registration)
    - 若用户已存在，比对 SHA-256 密码哈希。
    - 若用户不存在，自动注册并初始化密码。
    这降低了新用户的准入门槛，适合内部工具或 C 端轻量级产品。
    """
    pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    existing_hash = auth_repo.get_password_hash(user_id)
    if existing_hash:
        return existing_hash == pwd_hash
    auth_repo.create_user(user_id, pwd_hash)
    return True


def create_session(user_id: str, ttl_days: int = 30) -> str:
    """
    创建有状态的会话令牌 (Stateful Session Token)
    采用 UUIDv4 生成高熵 Token 防爆破，并在服务端设定过期时间 (TTL)。
    """
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
    """
    会话校验机制 (Session Validation)
    检查 Token 的存在性及过期时间。若已过期或格式异常，主动进行清理并拒绝放行。
    """
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
    """
    显式注销 (Explicit Logout)
    在服务端销毁对应的 Token 记录，阻断后续基于该 Token 的访问。
    """
    auth_repo.delete_session(token)
