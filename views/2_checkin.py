import streamlit as st
import time
from datetime import datetime
from streamlit.errors import StreamlitAPIException

from config import HARD_MODE_KEYWORDS
from ai_service import generate_feedback, generate_checkin_reply
from core.state import ensure_user_state
from core.user_context import load_user_context, UserStatus
from services.checkin_service import get_all_checkins, load_checkin, load_current_daily_tasks, save_checkin

# 获取当前用户 ID
user_id = st.session_state.user_id

ensure_user_state(user_id)
ctx = load_user_context(user_id)

st.title("✅ 今日打卡")
st.markdown("---")

today_str = datetime.now().strftime("%Y-%m-%d")
user_status = ctx.status

# 必须先完成问卷并且生成过任务才能打卡
if user_status == UserStatus.NOT_STARTED:
    st.info("请先前往「💬 AI咨询」页面完成基本信息并生成方案，之后即可在这里打卡。")
    if st.button("去咨询"):
        st.switch_page("views/1_consultation.py")
    st.stop()

latest_tasks = load_current_daily_tasks(user_id)
if not latest_tasks:
    st.info("当前还没有可打卡的任务。请先前往「💬 AI咨询」生成一份健康方案。")
    if st.button("去生成方案"):
        st.switch_page("views/1_consultation.py")
    st.stop()

completed_tasks, fb, ai_reply = load_checkin(user_id, today_str)

if completed_tasks or fb or ai_reply:
    if fb:
        st.success(f"🎉 今日已打卡：{fb}")
    else:
        st.success("🎉 今日已打卡")
    with st.expander("查看今日打卡详情", expanded=True):
        for t in latest_tasks:
            if t in completed_tasks:
                st.markdown(f"✅ **{t}**")
            else:
                st.markdown(f"⬜ {t}")
        if ai_reply:
            st.markdown(f"**💌 AI 的回应：**\n{ai_reply}")
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
            is_already_minimum = ctx.plan and ctx.plan.get("version_key") == "minimum"
            
            if is_hard_mode and not is_already_minimum:
                st.session_state.trigger_hard_mode = True
                st.rerun()
            
            with st.spinner("正在生成专属反馈..."):
                ai_reply = ""
                # 如果用户填写了感受，根据感受调用 AI 生成温暖回应
                if daily_feeling.strip():
                    try:
                        ai_reply = generate_checkin_reply(daily_feeling.strip(), checked_items, len(latest_tasks))
                    except Exception:
                        ai_reply = "我收到你的感受啦，无论今天过得怎么样，你都已经做得很好了，好好休息吧！"

                # 原有的反馈评价（根据完成任务数生成）
                feedback = generate_feedback(len(checked_items), len(latest_tasks))
                
                # 保存打卡记录（包含用户感受、生成的系统评价、以及 AI 回应）
                save_checkin(user_id, today_str, checked_items, feedback=daily_feeling, ai_reply=ai_reply or feedback)
                
                if ai_reply:
                    st.success("打卡成功！")
                    st.info(f"💌 **AI 寄语：**\n\n{ai_reply}")
                else:
                    st.success(feedback)
                
                time.sleep(2.5) # 给用户时间阅读 AI 回应
                st.rerun()

# 在表单外处理困难模式触发
if st.session_state.get("trigger_hard_mode"):
    st.warning("💚 我懂，改变习惯确实不容易。有时候觉得累、想放弃都是非常正常的。我们不需要一次做太多。")
    st.write("你想把目标调低一点吗？比如今天只做一件事：喝够水或早睡15分钟。")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("不用了，我可以坚持", use_container_width=True):
            st.session_state.trigger_hard_mode = False
            with st.spinner("正在生成专属反馈..."):
                feedback = generate_feedback(0, len(latest_tasks))
                save_checkin(user_id, today_str, [], feedback=daily_feeling, ai_reply=feedback)
            st.rerun()
    with c2:
        if st.button("好，帮我换成「最小行动方案」", use_container_width=True):
            st.session_state.trigger_hard_mode = False
            st.session_state.selected_plan_version = "minimum"
            st.session_state.generating_plan = True
            st.switch_page("views/1_consultation.py")

st.markdown("---")
st.subheader("📅 我的打卡日记")

# 历史打卡记录日历视图
history_records = get_all_checkins(user_id)

if not history_records:
    st.write("暂无过往打卡记录，今天是你迈出改变的第一步！")
else:
    for record in history_records:
        date_str = record["date"]
        tasks_done = record["tasks"]
        user_feedback = record["feedback"]
        ai_msg = record["ai_reply"]
        
        # 将日期字符串转为更友好的格式
        try:
            dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
            display_date = dt_obj.strftime("%Y年%m月%d日")
        except ValueError:
            display_date = date_str

        with st.expander(f"📌 {display_date} - 完成了 {len(tasks_done)} 项小目标", expanded=False):
            if tasks_done:
                st.markdown("**完成的行动：**")
                for t in tasks_done:
                    st.markdown(f"- ✅ {t}")
            else:
                st.markdown("那天在休息，没有完成任务，也没关系~")
                
            if user_feedback:
                st.markdown(f"> 📝 **你的感受：** {user_feedback}")
            
            if ai_msg:
                st.markdown(f"**💌 AI 的回应：**\n{ai_msg}")
