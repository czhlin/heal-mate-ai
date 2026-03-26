import streamlit as st

from core.consultation import build_question as _build_question
from core.consultation import ensure_chat_state
from core.state import ensure_user_state
from services.history_service import save_to_history as _save_to_history


def save_to_history(input_data, output_text, user_id="default"):
    _save_to_history(input_data, output_text, user_id=user_id)


def build_question(step, user_data, editing):
    return _build_question(step, user_data, editing)


def init_session_state():
    user_id = st.session_state.get("user_id")
    if not user_id:
        return

    ensure_user_state(user_id)
    ensure_chat_state(user_id)
