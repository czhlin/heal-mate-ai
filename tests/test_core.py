from core.user_context import UserStatus, get_user_status
from repos import user_state_repo


def test_get_user_status_not_started():
    # 确保测试前没有旧数据干扰
    user_state_repo.clear_user_state("test_user_not_started")
    status = get_user_status("test_user_not_started")
    assert status == UserStatus.NOT_STARTED


def test_get_user_status_profile_ready():
    # 确保没有旧数据干扰，然后插入只有 profile_id 的状态
    user_state_repo.clear_user_state("test_user_profile")
    user_state_repo.upsert_user_state(
        "test_user_profile", current_profile_id=1, current_plan_id=None, current_tasks_id=None
    )
    status = get_user_status("test_user_profile")
    assert status == UserStatus.PROFILE_READY


def test_get_user_status_plan_ready():
    # 用户有档案、有计划、有任务时
    user_state_repo.clear_user_state("test_user_plan")
    user_state_repo.upsert_user_state("test_user_plan", current_profile_id=1, current_plan_id=1, current_tasks_id=1)
    status = get_user_status("test_user_plan")
    assert status == UserStatus.PLAN_READY
