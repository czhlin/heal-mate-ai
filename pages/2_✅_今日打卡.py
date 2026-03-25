import streamlit as st
import time
from datetime import datetime

from database import load_latest_daily_tasks, load_checkin, save_checkin
from ai_service import generate_feedback
from utils import init_session_state

st.set_page_config(page_title="今日打卡", layout="centered")

init_session_state()

st.title("✅ 今日打卡")
st.markdown("---")

today_str = datetime.now().strftime("%Y-%m-%d")

# 必须先完成问卷并且生成过任务才能打卡
if not st.session_state.get("profile_complete"):
    st.info("请先前往「💬 AI咨询」页面完成基本信息并生成方案，之后即可在这里打卡。")
    if st.button("去咨询"):
        st.switch_page("pages/1_💬_AI咨询.py")
    st.stop()

latest_tasks = load_latest_daily_tasks()
if not latest_tasks:
    st.info("当前还没有可打卡的任务。请先前往「💬 AI咨询」生成一份健康方案。")
    if st.button("去生成方案"):
        st.switch_page("pages/1_💬_AI咨询.py")
    st.stop()

completed_tasks, fb = load_checkin(today_str)

if fb:
    st.success(f"🎉 今日已打卡：{fb}")
    with st.expander("查看今日打卡详情", expanded=True):
        for t in latest_tasks:
            if t in completed_tasks:
                st.markdown(f"✅ **{t}**")
            else:
                st.markdown(f"⬜ {t}")
else:
    with st.form("daily_checkin_form"):
        st.write("### 勾选你今天完成的任务：")
        checked_items = []
        for t in latest_tasks:
            if st.checkbox(t, key=f"task_{t}"):
                checked_items.append(t)
        
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 提交今日打卡", use_container_width=True)
        
        if submitted:
            with st.spinner("正在生成专属反馈..."):
                feedback = generate_feedback(len(checked_items), len(latest_tasks))
                save_checkin(today_str, checked_items, feedback)
                st.success(feedback)
                time.sleep(1.5)
                st.rerun()