import streamlit as st
import time
from datetime import datetime
from streamlit.errors import StreamlitAPIException

from database import load_latest_daily_tasks, load_checkin, save_checkin, load_latest_plan
from config import HARD_MODE_KEYWORDS
from ai_service import generate_feedback
from utils import init_session_state

# 获取当前用户 ID
user_id = st.session_state.user_id

init_session_state()

st.title("✅ 今日打卡")
st.markdown("---")

today_str = datetime.now().strftime("%Y-%m-%d")

# 必须先完成问卷并且生成过任务才能打卡
if not st.session_state.get("profile_complete"):
    st.info("请先前往「💬 AI咨询」页面完成基本信息并生成方案，之后即可在这里打卡。")
    if st.button("去咨询"):
        st.switch_page("views/1_consultation.py")
    st.stop()

latest_tasks = load_latest_daily_tasks(user_id)
if not latest_tasks:
    st.info("当前还没有可打卡的任务。请先前往「💬 AI咨询」生成一份健康方案。")
    if st.button("去生成方案"):
        st.switch_page("views/1_consultation.py")
    st.stop()

completed_tasks, fb = load_checkin(user_id, today_str)

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
        
        # 新增每日随感文本框，以便检测困难模式
        daily_feeling = st.text_input("今天感觉怎么样？（选填，比如：太累了不想动）")
        
        submitted = st.form_submit_button("🚀 提交今日打卡", use_container_width=True)
        
        if submitted:
            # 检测是否触发困难模式
            is_hard_mode = False
            if daily_feeling and any(kw in daily_feeling for kw in HARD_MODE_KEYWORDS):
                is_hard_mode = True
            if len(checked_items) == 0 and len(latest_tasks) > 0:
                is_hard_mode = True
            
            # 如果当前已经是 minimum，就不需要再提示降级了
            current_plan = load_latest_plan(user_id)
            is_already_minimum = current_plan and current_plan.get("version_key") == "minimum"
            
            if is_hard_mode and not is_already_minimum:
                st.session_state.trigger_hard_mode = True
                st.rerun()
            
            with st.spinner("正在生成专属反馈..."):
                feedback = generate_feedback(len(checked_items), len(latest_tasks))
                save_checkin(user_id, today_str, checked_items, feedback)
                st.success(feedback)
                time.sleep(1.5)
                st.rerun()

# 在表单外处理困难模式触发
if st.session_state.get("trigger_hard_mode"):
    st.warning("💚 我懂，改变习惯确实不容易。有时候觉得累、想放弃都是非常正常的。我们不需要一次做太多。")
    st.write("你想把目标调低一点吗？比如今天只做一件事：喝够水或早睡15分钟。")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("不用了，我可以坚持", use_container_width=True):
            st.session_state.trigger_hard_mode = False
            # 直接按0任务提交并生成反馈
            with st.spinner("正在生成专属反馈..."):
                feedback = generate_feedback(0, len(latest_tasks))
                save_checkin(user_id, today_str, [], feedback)
            st.rerun()
    with c2:
        if st.button("好，帮我换成「最小行动方案」", use_container_width=True):
            st.session_state.trigger_hard_mode = False
            st.session_state.selected_plan_version = "minimum"
            st.session_state.generating_plan = True
            st.switch_page("views/1_consultation.py")
