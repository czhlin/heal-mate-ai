from ai_service import extract_daily_tasks, generate_plan
from repos import plan_repo, tasks_repo


def generate_and_save_plan(user_id: str, user_data: dict, version_key: str):
    plan_text = generate_plan(user_data, version_key)
    tasks = extract_daily_tasks(plan_text)
    tasks_repo.save_daily_tasks(user_id, tasks)
    plan_repo.save_plan(user_id, version_key, plan_text)
    return plan_text, tasks


def load_latest_plan(user_id: str):
    return plan_repo.load_latest_plan(user_id)

