from repos import checkin_repo, tasks_repo


def load_latest_daily_tasks(user_id: str):
    return tasks_repo.load_latest_daily_tasks(user_id)


def load_checkin(user_id: str, check_date: str):
    return checkin_repo.load_checkin(user_id, check_date)


def save_checkin(user_id: str, check_date: str, completed_tasks_list: list, feedback: str = "", ai_reply: str = ""):
    checkin_repo.save_checkin(user_id, check_date, completed_tasks_list, feedback=feedback, ai_reply=ai_reply)


def get_all_checkins(user_id: str):
    return checkin_repo.get_all_checkins(user_id)


def get_last_checkin_date(user_id: str):
    return checkin_repo.get_last_checkin_date(user_id)

