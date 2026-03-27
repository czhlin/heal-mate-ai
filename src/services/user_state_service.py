from datetime import datetime

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


def set_current_tasks(user_id: str, tasks_id: int):
    user_state_repo.upsert_user_state(user_id, current_tasks_id=tasks_id)


def set_short_term_state(user_id: str, state_key: str, note: str, expires_at: str):
    user_state_repo.upsert_user_state(
        user_id,
        short_term_state=state_key,
        short_term_note=note,
        short_term_expires_at=expires_at,
    )


def clear_short_term_state(user_id: str):
    user_state_repo.upsert_user_state(user_id, short_term_state="", short_term_note="", short_term_expires_at="")


def get_active_short_term_state(user_id: str):
    s = get_user_state(user_id) or {}
    state_key = (s.get("short_term_state") or "").strip()
    expires_at = (s.get("short_term_expires_at") or "").strip()
    if not state_key or not expires_at:
        return None
    try:
        exp = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
        if exp <= datetime.now():
            return None
    except ValueError:
        return None
    return {"state": state_key, "note": s.get("short_term_note") or "", "expires_at": expires_at}


def clear_user_state(user_id: str):
    user_state_repo.clear_user_state(user_id)
