"""
领域核心层 (Core Domain): 咨询流与对话状态控制

此模块负责处理 AI 问诊阶段的对话流控 (Conversation Flow Control)。
通过维护一个步进式状态机 (Step-by-Step State Machine)，
将用户离散的对话输入转化为结构化的用户档案 (User Profile)。
"""

import streamlit as st
from config import QUESTIONS
from services.profile_service import load_latest_user_profile, load_user_profile_by_id
from services.user_state_service import get_user_state


def build_question(step, user_data, editing):
    """
    提示词构建器 (Prompt Builder)
    动态生成下一步的提问内容。如果是编辑模式，则提供当前值的回显与保留机制。
    """
    q = QUESTIONS[step]["question"]
    if editing:
        key = QUESTIONS[step]["key"]
        current_value = (user_data.get(key) or "").strip()
        if current_value:
            q = f"{q}\n\n（当前：{current_value}；输入“跳过”保持不变）"
    return q


def ensure_chat_state(user_id: str):
    """
    聊天会话恢复器 (Chat Session Restorer)
    系统初始化或页面刷新时调用。
    职责：
    1. 探测底层是否有持久化的 Profile。
    2. 若有，通过历史数据重建完整的聊天上下文（History Rehydration），将对话进度直接快进至完成态。
    3. 若无，初始化对话流的零状态（Zero State）。
    """
    if not user_id:
        return

    if "current_step" not in st.session_state:
        st.session_state.current_step = 0
    if "messages" in st.session_state:
        return

    s = get_user_state(user_id) or {}
    current_profile_id = s.get("current_profile_id")
    if current_profile_id:
        latest = load_user_profile_by_id(current_profile_id)
    else:
        latest = load_latest_user_profile(user_id)

    if latest:
        # Rehydration: 将结构化档案反向渲染为对话流
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
    else:
        # 初始化第一步交互
        st.session_state.editing = False
        st.session_state.messages = [{"role": "assistant", "content": build_question(0, {}, False)}]
