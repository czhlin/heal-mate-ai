import streamlit as st

from services.profile_service import load_latest_user_profile


def ensure_user_state(user_id: str):
    if not user_id:
        return

    if "user_data" not in st.session_state:
        st.session_state.user_data = {}
    if "profile_complete" not in st.session_state:
        st.session_state.profile_complete = False
    if "editing" not in st.session_state:
        st.session_state.editing = False
    if "selected_plan_version" not in st.session_state:
        st.session_state.selected_plan_version = None
    if "plan_text" not in st.session_state:
        st.session_state.plan_text = None
    if "generating_plan" not in st.session_state:
        st.session_state.generating_plan = False

    latest = load_latest_user_profile(user_id)
    if latest:
        st.session_state.user_data = latest
        st.session_state.profile_complete = True

