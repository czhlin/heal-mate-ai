from repos import profile_repo


def save_user_profile(user_id: str, user_data: dict):
    profile_repo.save_user_profile(user_id, user_data)


def load_latest_user_profile(user_id: str):
    return profile_repo.load_latest_user_profile(user_id)


def clear_user_profiles(user_id: str):
    profile_repo.clear_user_profiles(user_id)

