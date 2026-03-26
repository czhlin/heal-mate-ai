from repos import checkin_repo, tasks_repo
from repos import user_state_repo


def load_latest_daily_tasks(user_id: str):
    return tasks_repo.load_latest_daily_tasks(user_id)


def load_current_daily_tasks(user_id: str):
    s = user_state_repo.get_user_state(user_id) or {}
    tasks_id = s.get("current_tasks_id")
    if tasks_id:
        return tasks_repo.load_daily_tasks_by_id(tasks_id)
    return tasks_repo.load_latest_daily_tasks(user_id)


def load_checkin(user_id: str, check_date: str):
    return checkin_repo.load_checkin(user_id, check_date)


def save_checkin(user_id: str, check_date: str, completed_tasks_list: list, feedback: str = "", ai_reply: str = ""):
    checkin_repo.save_checkin(user_id, check_date, completed_tasks_list, feedback=feedback, ai_reply=ai_reply)


def get_all_checkins(user_id: str):
    return checkin_repo.get_all_checkins(user_id)


def get_last_checkin_date(user_id: str):
    return checkin_repo.get_last_checkin_date(user_id)
