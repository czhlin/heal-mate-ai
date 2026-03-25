import streamlit as st
import time

from config import DEEPSEEK_API_KEY, QUESTIONS, PLAN_VERSIONS
from database import (
    save_user_profile,
    load_latest_user_profile,
    clear_user_profiles,
    save_daily_tasks,
    save_plan,
)
from ai_service import generate_plan, extract_daily_tasks
from utils import save_to_history, init_session_state, build_question

# 获取当前用户 ID
user_id = st.session_state.user_id

# 初始化状态
init_session_state()

st.title("💬 AI健康管家")
st.markdown("---")

# 检查 API Key
if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "dummy_key":
    st.error("⚠️ 未检测到 DEEPSEEK_API_KEY。请在环境变量中配置后重试。")
    st.stop()

# 侧边栏
with st.sidebar:
    st.header("📖 使用说明")
    st.markdown("""
    欢迎使用 HealMate-AI！
    请在聊天框中与我对话，我会一步步了解你的情况。
    收集完信息后，我将为你量身定制一份可执行的健康方案。
    """)
    if st.button("🔄 重新开始对话"):
        st.session_state.clear()
        st.rerun()
    if st.button("✏️ 修改信息"):
        latest = load_latest_user_profile(user_id) or st.session_state.get("user_data") or {}
        st.session_state.user_data = latest
        st.session_state.messages = [
            {"role": "assistant", "content": build_question(0, latest, True)}
        ]
        st.session_state.current_step = 0
        st.session_state.profile_complete = False
        st.session_state.selected_plan_version = None
        st.session_state.plan_text = None
        st.session_state.generating_plan = False
        st.session_state.editing = True
        st.rerun()
    if st.button("🧹 重置信息"):
        clear_user_profiles(user_id)
        st.session_state.clear()
        st.session_state.user_id = user_id  # 保持登录状态
        st.rerun()

# 渲染聊天记录
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 问答流程
if st.session_state.current_step < len(QUESTIONS):
    user_input = st.chat_input("输入你的回答...")
    if user_input:
        user_input = user_input.strip()
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
            
        current_q = QUESTIONS[st.session_state.current_step]
        key = current_q["key"]
        if st.session_state.editing and user_input == "跳过":
            reply_text = "好的，保持不变。"
        else:
            st.session_state.user_data[key] = user_input
            reply_text = current_q["reply"]
        
        st.session_state.current_step += 1
        
        if st.session_state.current_step < len(QUESTIONS):
            next_q_text = build_question(
                st.session_state.current_step, st.session_state.user_data, st.session_state.editing
            )
            ai_msg = f"{reply_text}\n\n{next_q_text}"
        else:
            st.session_state.editing = False
            st.session_state.profile_complete = True
            save_user_profile(user_id, st.session_state.user_data)
            ai_msg = f"{reply_text}\n\n感谢你的分享！我现在为你生成个性化方案。你想要哪个版本？"
            
        st.session_state.messages.append({"role": "assistant", "content": ai_msg})
        with st.chat_message("assistant"):
            st.markdown(ai_msg)
            
        st.rerun()

# 分层方案生成 UI
if st.session_state.profile_complete and not st.session_state.editing:
    st.markdown("---")
    st.subheader("选择方案版本")
    c1, c2, c3 = st.columns(3)
    clicked = None
    with c1:
        if st.button(f"{PLAN_VERSIONS['ideal']['button']}\n\n{PLAN_VERSIONS['ideal']['hint']}"):
            clicked = "ideal"
    with c2:
        if st.button(f"{PLAN_VERSIONS['lazy']['button']}\n\n{PLAN_VERSIONS['lazy']['hint']}"):
            clicked = "lazy"
    with c3:
        if st.button(f"{PLAN_VERSIONS['free']['button']}\n\n{PLAN_VERSIONS['free']['hint']}"):
            clicked = "free"

    if clicked:
        st.session_state.selected_plan_version = clicked
        st.session_state.generating_plan = True

    if st.session_state.generating_plan and st.session_state.selected_plan_version:
        version = PLAN_VERSIONS.get(st.session_state.selected_plan_version) or PLAN_VERSIONS["ideal"]
        with st.chat_message("assistant"):
            with st.spinner(f"🧠 正在生成 {version['label']} ..."):
                try:
                    latest_profile = load_latest_user_profile(user_id) or st.session_state.user_data
                    plan = generate_plan(latest_profile, st.session_state.selected_plan_version)
                    
                    # 提取打卡任务并保存
                    tasks = extract_daily_tasks(plan)
                    save_daily_tasks(user_id, tasks)
                    save_plan(user_id, st.session_state.selected_plan_version, plan)
                    
                    st.session_state.plan_text = plan
                    st.session_state.generating_plan = False

                    header = f"### 当前版本：{version['label']}"
                    message = f"{header}\n\n{plan}"
                    save_to_history(latest_profile, message)
                    st.session_state.messages.append({"role": "assistant", "content": message})
                    st.rerun()
                except Exception as e:
                    st.session_state.generating_plan = False
                    st.error(f"抱歉，生成方案时遇到了问题：{str(e)}")
