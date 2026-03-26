from dataclasses import dataclass
from enum import Enum
from typing import Any
from services.user_state_service import get_user_state

from services.profile_service import load_latest_user_profile, load_user_profile_by_id
from services.plan_service import load_latest_plan, load_plan_by_id
from repos.tasks_repo import load_daily_tasks_by_id, load_latest_daily_tasks


class UserStatus(Enum):

    NOT_STARTED = "NOT_STARTED"
    PROFILE_READY = "PROFILE_READY"
    PLAN_READY = "PLAN_READY"


def get_user_status(user_id: str) -> UserStatus:

    state = get_user_state(user_id)
    if not state:
        return UserStatus.NOT_STARTED

    if state.get("current_plan_id") and state.get("current_tasks_id"):
        return UserStatus.PLAN_READY
    
    if state.get("current_profile_id"):
        return UserStatus.PROFILE_READY
        
    return UserStatus.NOT_STARTED


@dataclass(frozen=True)
class UserContext:
    user_id: str
    state: dict[str, Any]
    status: UserStatus
    profile: dict[str, Any] | None
    plan: dict[str, Any] | None
    tasks: list


def load_user_context(user_id: str) -> UserContext:
    state = get_user_state(user_id) or {}
    status = get_user_status(user_id)

    profile = None
    current_profile_id = state.get("current_profile_id")
    if current_profile_id:
        profile = load_user_profile_by_id(current_profile_id)
    if profile is None:
        profile = load_latest_user_profile(user_id)

    plan = None
    current_plan_id = state.get("current_plan_id")
    if current_plan_id:
        plan = load_plan_by_id(current_plan_id)
    if plan is None:
        plan = load_latest_plan(user_id)

    tasks = []
    current_tasks_id = state.get("current_tasks_id")
    if current_tasks_id:
        tasks = load_daily_tasks_by_id(current_tasks_id)
    if not tasks:
        tasks = load_latest_daily_tasks(user_id)

    return UserContext(
        user_id=user_id,
        state=state,
        status=status,
        profile=profile,
        plan=plan,
        tasks=tasks,
    )
