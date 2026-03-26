from ai_service import extract_daily_tasks, generate_plan
from repos import plan_repo, tasks_repo
from services.user_state_service import set_current_plan_and_tasks


def generate_and_save_plan(user_id: str, user_data: dict, version_key: str):
    plan_text = generate_plan(user_data, version_key)
    tasks = extract_daily_tasks(plan_text)
    tasks_id = tasks_repo.save_daily_tasks(user_id, tasks)
    plan_id = plan_repo.save_plan(user_id, version_key, plan_text)
    if plan_id and tasks_id:
        set_current_plan_and_tasks(user_id, plan_id, tasks_id)
    return plan_text, tasks


def load_latest_plan(user_id: str):
    return plan_repo.load_latest_plan(user_id)


def load_plan_by_id(plan_id: int):
    return plan_repo.load_plan_by_id(plan_id)
