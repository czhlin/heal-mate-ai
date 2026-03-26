import streamlit as st

from services.profile_service import load_latest_user_profile, load_user_profile_by_id
from services.user_state_service import get_user_state
from core.user_context import get_user_status, UserStatus


def ensure_user_state(user_id: str):
    if not user_id:
        return

    if "user_data" not in st.session_state:
        st.session_state.user_data = {}
    if "editing" not in st.session_state:
        st.session_state.editing = False
    if "selected_plan_version" not in st.session_state:
        st.session_state.selected_plan_version = None
    if "plan_text" not in st.session_state:
        st.session_state.plan_text = None
    if "generating_plan" not in st.session_state:
        st.session_state.generating_plan = False

    s = get_user_state(user_id) or {}
    current_profile_id = s.get("current_profile_id")
    if current_profile_id:
        profile = load_user_profile_by_id(current_profile_id)
    else:
        profile = load_latest_user_profile(user_id)
    if profile:
        st.session_state.user_data = profile
