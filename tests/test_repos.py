import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from repos import auth_repo, profile_repo, user_state_repo


def test_auth_repo_create_and_get():
    # 测试插入和获取密码哈希
    user_id = "test_user_unique"
    pwd_hash = "fake_hash_123"

    # 确保没有旧数据
    from repos.connection import connect

    conn = connect()
    try:
        conn.execute("DELETE FROM auth WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()

    auth_repo.create_user(user_id, pwd_hash)
    retrieved_hash = auth_repo.get_password_hash(user_id)

    assert retrieved_hash == pwd_hash


def test_auth_repo_session():
    # 测试会话的创建、获取与删除
    user_id = "test_user"
    token = "fake_token_abc"
    created_at = "2026-01-01 10:00:00"
    expires_at = "2026-01-31 10:00:00"

    auth_repo.insert_session(token, user_id, created_at, expires_at)

    session = auth_repo.get_session(token)
    assert session is not None
    assert session["user_id"] == user_id
    assert session["expires_at"] == expires_at

    auth_repo.delete_session(token)
    assert auth_repo.get_session(token) is None


def test_profile_repo_save_and_load():
    user_id = "test_user"
    profile_data = {
        "basic_info": "180cm, 75kg",
        "goal": "减肥",
        "diet": "普通",
        "allergies": "无",
        "grocery": "超市",
        "kitchenware": "平底锅",
        "cooking_time": "30分钟",
    }

    profile_id = profile_repo.save_user_profile(user_id, profile_data)
    assert profile_id > 0

    loaded_profile = profile_repo.load_user_profile_by_id(profile_id)
    assert loaded_profile is not None
    assert loaded_profile["basic_info"] == profile_data["basic_info"]
    assert loaded_profile["goal"] == profile_data["goal"]


def test_user_state_repo_upsert():
    user_id = "state_user_unique"
    user_state_repo.clear_user_state(user_id)

    # 第一次插入
    user_state_repo.upsert_user_state(user_id, current_profile_id=10, current_plan_id=None, current_tasks_id=None)
    state = user_state_repo.get_user_state(user_id)
    assert state["current_profile_id"] == 10
    assert state["current_plan_id"] is None

    # 更新其他字段，不覆盖原有字段
    user_state_repo.upsert_user_state(user_id, current_plan_id=20, current_tasks_id=30)
    state = user_state_repo.get_user_state(user_id)
    assert state["current_profile_id"] == 10
    assert state["current_plan_id"] == 20
    assert state["current_tasks_id"] == 30
