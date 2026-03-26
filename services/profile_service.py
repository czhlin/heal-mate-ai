from repos import profile_repo
from services.user_state_service import clear_user_state, set_current_profile


def save_user_profile(user_id: str, user_data: dict):
    profile_id = profile_repo.save_user_profile(user_id, user_data)
    if profile_id:
        set_current_profile(user_id, profile_id)
    return profile_id


def load_latest_user_profile(user_id: str):
    return profile_repo.load_latest_user_profile(user_id)


def load_user_profile_by_id(profile_id: int):
    return profile_repo.load_user_profile_by_id(profile_id)


def clear_user_profiles(user_id: str):
    profile_repo.clear_user_profiles(user_id)
    clear_user_state(user_id)
