"""
领域核心层 (Core Domain): 视图状态管理

此模块主要充当 Domain Model 与 Streamlit UI Session State 之间的适配器。
负责将后端的持久化状态（如 Profile）映射并初始化到前端交互所需的内存状态中，
确保用户在页面间切换时，局部组件（如编辑模式、选中版本等）状态的一致性与可控性。
"""

import streamlit as st
from services.profile_service import load_latest_user_profile, load_user_profile_by_id
from services.user_state_service import get_user_state


def ensure_user_state(user_id: str):
    """
    状态同步屏障 (State Synchronization Barrier):
    在进入关键视图前调用，保证必需的 UI 会话级状态已被安全初始化。
    同时，它会按需从 Repository 层惰性加载最新的用户档案，同步到 session_state 中。
    """
    if not user_id:
        return

    # 初始化 UI 交互状态默认值
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

    # 同步领域对象到 UI 会话
    s = get_user_state(user_id) or {}
    current_profile_id = s.get("current_profile_id")
    if current_profile_id:
        profile = load_user_profile_by_id(current_profile_id)
    else:
        profile = load_latest_user_profile(user_id)
    if profile:
        st.session_state.user_data = profile
