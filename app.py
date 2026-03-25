import streamlit as st
import time
from datetime import datetime

# 导入抽离的模块
from config import DEEPSEEK_API_KEY, QUESTIONS, PLAN_VERSIONS
from database import (
    init_db,
    save_user_profile,
    load_latest_user_profile,
    clear_user_profiles,
    save_daily_tasks,
    load_latest_daily_tasks,
    save_checkin,
    load_checkin,
    get_last_checkin_date,
)
from ai_service import generate_plan, extract_daily_tasks, generate_feedback
from utils import save_to_history

# 初始化数据库
init_db()

# 设置页面配置
st.set_page_config(page_title="AI健康管家", layout="centered")

# 添加自定义 CSS 优化界面
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem !important;
        font-weight: 700;
        color: #0E1117;
        margin-bottom: 1rem;
        text-align: center;
    }
    .chat-container {
        padding-bottom: 100px;
    }
    </style>
    """, unsafe_allow_html=True)

def build_question(step, user_data, editing):
    q = QUESTIONS[step]["question"]
    if editing:
        key = QUESTIONS[step]["key"]
        current_value = (user_data.get(key) or "").strip()
        if current_value:
            q = f"{q}\n\n（当前：{current_value}；输入“跳过”保持不变）"
    return q

def init_session_state():
    if "messages" not in st.session_state:
        latest = load_latest_user_profile()
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

init_session_state()

# 侧边栏
with st.sidebar:
    st.header("📖 使用说明")
    st.markdown("""
    欢迎使用 HealMate-AI！
    请在聊天框中与我对话，我会一步步了解你的情况。
    收集完信息后，我将为你量身定制一份可执行的健康方案。
    
    如果你想重新开始，请点击下方按钮。
    """)
    if st.button("🔄 重新开始对话"):
        st.session_state.clear()
        st.rerun()
    if st.button("✏️ 修改信息"):
        latest = load_latest_user_profile() or st.session_state.get("user_data") or {}
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
        clear_user_profiles()
        st.session_state.clear()
        st.rerun()
    
    st.markdown("---")
    st.header("⚠️ 免责声明")
    st.info("""
    本应用生成的所有内容仅供参考，不构成医疗建议、诊断或治疗方案。
    在开始任何新的饮食或运动计划之前，请务必咨询专业医生的意见。
    """)

# 页面标题
st.markdown('<h1 class="main-title">AI健康管家 🩺</h1>', unsafe_allow_html=True)
st.markdown("---")

# 检查 API Key
if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "dummy_key":
    st.error("⚠️ 未检测到 DEEPSEEK_API_KEY。请在环境变量中配置后重试。")
    st.stop()

# ----- 提醒与打卡模块 -----
today_str = datetime.now().strftime("%Y-%m-%d")

# 1. 检查连续未打卡
last_checkin = get_last_checkin_date()
if last_checkin and st.session_state.get("profile_complete"):
    last_date = datetime.strptime(last_checkin, "%Y-%m-%d").date()
    today_date = datetime.now().date()
    if (today_date - last_date).days >= 2:
        st.info("💚 我注意到你最近没打卡，是遇到困难了吗？没关系，休息一下，随时可以重新开始。需要调整目标的话，可以在左侧点击“修改信息”。")

# 2. 渲染今日任务打卡 UI
if st.session_state.get("profile_complete") and not st.session_state.get("editing"):
    latest_tasks = load_latest_daily_tasks()
    if latest_tasks:
        completed_tasks, fb = load_checkin(today_str)
        
        st.subheader("📋 今日任务")
        if fb:
            st.success(f"今日已打卡：{fb}")
            with st.expander("查看今日打卡详情"):
                for t in latest_tasks:
                    if t in completed_tasks:
                        st.markdown(f"✅ {t}")
                    else:
                        st.markdown(f"⬜ {t}")
        else:
            with st.form("daily_checkin_form"):
                st.write("勾选你今天完成的任务：")
                checked_items = []
                for t in latest_tasks:
                    # 使用任务文本作为 key 确保唯一性
                    if st.checkbox(t, key=f"task_{t}"):
                        checked_items.append(t)
                
                submitted = st.form_submit_button("提交今日打卡")
                if submitted:
                    with st.spinner("正在生成反馈..."):
                        feedback = generate_feedback(len(checked_items), len(latest_tasks))
                        save_checkin(today_str, checked_items, feedback)
                        st.success(feedback)
                        time.sleep(1.5)
                        st.rerun()
        st.markdown("---")
# -------------------------

# 渲染聊天记录
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 如果还没到最后一步，显示输入框
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
            save_user_profile(st.session_state.user_data)
            ai_msg = f"{reply_text}\n\n感谢你的分享！我现在为你生成个性化方案。你想要哪个版本？"
            
        st.session_state.messages.append({"role": "assistant", "content": ai_msg})
        with st.chat_message("assistant"):
            st.markdown(ai_msg)
            
        st.rerun()

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
                    latest_profile = load_latest_user_profile() or st.session_state.user_data
                    plan = generate_plan(latest_profile, st.session_state.selected_plan_version)
                    
                    # 提取打卡任务并保存
                    tasks = extract_daily_tasks(plan)
                    save_daily_tasks(tasks)
                    
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
