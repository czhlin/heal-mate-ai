from enum import Enum
from services.user_state_service import get_user_state

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
