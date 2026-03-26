from datetime import datetime, timedelta

from repos import auth_repo, checkin_repo
from services import auth_service, checkin_service


def test_verify_or_create_user_new():
    user_id = "new_user"
    password = "secure_password"

    # 第一次登录应该是创建并返回 True
    result = auth_service.verify_or_create_user(user_id, password)
    assert result is True

    # 第二次使用正确密码登录
    result = auth_service.verify_or_create_user(user_id, password)
    assert result is True

    # 使用错误密码登录
    result = auth_service.verify_or_create_user(user_id, "wrong_password")
    assert result is False


def test_create_and_get_session():
    user_id = "session_user"
    token = auth_service.create_session(user_id, ttl_days=1)

    assert token is not None

    retrieved_user_id = auth_service.get_user_id_by_session(token)
    assert retrieved_user_id == user_id

    # 注销后应当无法获取
    auth_service.delete_session(token)
    assert auth_service.get_user_id_by_session(token) is None


def test_expired_session_is_rejected(mocker):
    user_id = "expired_user"
    # 创建一个过期的 session
    now = datetime.now()
    token = "expired_token_123"
    expires_at = now - timedelta(days=1)

    auth_repo.insert_session(
        token,
        user_id,
        now.strftime("%Y-%m-%d %H:%M:%S"),
        expires_at.strftime("%Y-%m-%d %H:%M:%S"),
    )

    # 获取时应该返回 None，并且从数据库中清理掉
    assert auth_service.get_user_id_by_session(token) is None
    assert auth_repo.get_session(token) is None


def test_checkin_service_save_and_load():
    user_id = "checkin_user"
    today = datetime.now().date().strftime("%Y-%m-%d")

    # 清理可能存在的旧数据
    checkin_repo.conn = checkin_repo.connect()
    try:
        checkin_repo.conn.execute("DELETE FROM check_ins WHERE user_id = ?", (user_id,))
        checkin_repo.conn.commit()
    finally:
        checkin_repo.conn.close()

    # 模拟打卡
    tasks = ["喝水", "睡觉"]
    checkin_service.save_checkin(user_id, today, tasks, "很好", "AI的回复")

    # 获取所有打卡记录
    all_checkins = checkin_service.get_all_checkins(user_id)
    assert len(all_checkins) == 1

    # 根据 repos/checkin_repo.py 中的 get_all_checkins，
    # 它返回的结构是包含字典的列表，且日期字段的 key 为 "date" 而不是 "check_date"。
    assert all_checkins[0]["date"] == today

    # 获取最后打卡日期
    last_date = checkin_service.get_last_checkin_date(user_id)
    assert last_date == today
