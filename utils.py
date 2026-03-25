import os
import json
import streamlit as st
from datetime import datetime
from database import load_latest_user_profile
from config import QUESTIONS, HISTORY_PATH

def save_to_history(input_data, output_text, user_id="default"):
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_id,
        "input": input_data,
        "output": output_text
    }
    history_list = []
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                history_list = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    history_list.append(record)
    try:
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history_list, f, ensure_ascii=False, indent=4)
    except IOError as e:
        print(f"保存历史记录失败: {str(e)}")

def build_question(step, user_data, editing):
    q = QUESTIONS[step]["question"]
    if editing:
        key = QUESTIONS[step]["key"]
        current_value = (user_data.get(key) or "").strip()
        if current_value:
            q = f"{q}\n\n（当前：{current_value}；输入“跳过”保持不变）"
    return q

def init_session_state():
    user_id = st.session_state.get("user_id")
    if not user_id:
        return
        
    if "messages" not in st.session_state:
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
            st.session_state.messages = [
                {"role": "assistant", "content": build_question(0, {}, False)}
            ]
            st.session_state.profile_complete = False
            
    if "current_step" not in st.session_state:
        st.session_state.current_step = 0
    if "user_data" not in st.session_state:
        st.session_state.user_data = {}
    if "editing" not in st.session_state:
        st.session_state.editing = False
    if "profile_complete" not in st.session_state:
        st.session_state.profile_complete = False
    if "selected_plan_version" not in st.session_state:
        st.session_state.selected_plan_version = None
    if "plan_text" not in st.session_state:
        st.session_state.plan_text = None
    if "generating_plan" not in st.session_state:
        st.session_state.generating_plan = False