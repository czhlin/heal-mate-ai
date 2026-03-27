from repos import checkin_repo, tasks_repo
from services.user_state_service import get_user_state


def load_latest_daily_tasks(user_id: str):
    return tasks_repo.load_latest_daily_tasks(user_id)


def load_current_daily_tasks(user_id: str):
    s = get_user_state(user_id) or {}
    tasks_id = s.get("current_tasks_id")
    if tasks_id:
        return tasks_repo.load_daily_tasks_by_id(tasks_id)
    return tasks_repo.load_latest_daily_tasks(user_id)


def load_checkin(user_id: str, check_date: str):
    return checkin_repo.load_checkin(user_id, check_date)


def save_checkin(
    user_id: str,
    check_date: str,
    completed_tasks_list: list,
    feedback: str = "",
    ai_reply: str = "",
    tasks_snapshot_list=None,
    tasks_total_count=None,
):
    checkin_repo.save_checkin(
        user_id,
        check_date,
        completed_tasks_list,
        feedback=feedback,
        ai_reply=ai_reply,
        tasks_snapshot_list=tasks_snapshot_list,
        tasks_total_count=tasks_total_count,
    )


def get_all_checkins(user_id: str):
    return checkin_repo.get_all_checkins(user_id)


def get_last_checkin_date(user_id: str):
    return checkin_repo.get_last_checkin_date(user_id)
