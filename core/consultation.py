import streamlit as st

from config import QUESTIONS
from services.profile_service import load_latest_user_profile


def build_question(step, user_data, editing):
    q = QUESTIONS[step]["question"]
    if editing:
        key = QUESTIONS[step]["key"]
        current_value = (user_data.get(key) or "").strip()
        if current_value:
            q = f"{q}\n\n（当前：{current_value}；输入“跳过”保持不变）"
    return q


def ensure_chat_state(user_id: str):
    if not user_id:
        return

    if "current_step" not in st.session_state:
        st.session_state.current_step = 0
    if "messages" in st.session_state:
        return

    latest = load_latest_user_profile(user_id)
    if latest:
        st.session_state.user_data = latest
        st.session_state.editing = False
        msgs = []
        for item in QUESTIONS:
            msgs.append({"role": "assistant", "content": item["question"]})
            v = (latest.get(item["key"]) or "").strip()
            if v:
                msgs.append({"role": "user", "content": v})
                msgs.append({"role": "assistant", "content": item["reply"]})
        msgs.append(
            {
                "role": "assistant",
                "content": "我已加载你上次的用户信息。你可以在侧边栏点击“修改信息”来更新，或点击“重置信息”清空数据重新开始。也可以直接选择一个版本生成分层方案。",
            }
        )
        st.session_state.messages = msgs
        st.session_state.current_step = len(QUESTIONS)
        st.session_state.profile_complete = True
    else:
        st.session_state.editing = False
        st.session_state.messages = [{"role": "assistant", "content": build_question(0, {}, False)}]
        st.session_state.profile_complete = False

