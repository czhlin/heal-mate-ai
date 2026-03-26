from repos import user_state_repo


def get_user_state(user_id: str):
    return user_state_repo.get_user_state(user_id)


def has_profile(user_id: str) -> bool:
    s = get_user_state(user_id) or {}
    return bool(s.get("current_profile_id"))


def has_plan(user_id: str) -> bool:
    s = get_user_state(user_id) or {}
    return bool(s.get("current_plan_id"))


def has_tasks(user_id: str) -> bool:
    s = get_user_state(user_id) or {}
    return bool(s.get("current_tasks_id"))


def set_current_profile(user_id: str, profile_id: int):
    user_state_repo.upsert_user_state(user_id, current_profile_id=profile_id)


def set_current_plan_and_tasks(user_id: str, plan_id: int, tasks_id: int):
    user_state_repo.upsert_user_state(user_id, current_plan_id=plan_id, current_tasks_id=tasks_id)


def clear_user_state(user_id: str):
    user_state_repo.clear_user_state(user_id)

