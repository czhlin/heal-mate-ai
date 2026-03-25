import streamlit as st
from datetime import datetime
from database import init_db, get_last_checkin_date
from utils import init_session_state

# 初始化数据库
init_db()

# 设置页面配置
st.set_page_config(page_title="AI健康管家 - 首页", layout="centered", page_icon="🩺")

# 初始化 session state
init_session_state()

# 自定义 CSS 优化首页卡片和布局
st.markdown("""
    <style>
    .main-title {
        font-size: 3rem !important;
        font-weight: 800;
        color: #0E1117;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    .sub-title {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    div.stButton > button:first-child {
        height: 80px;
        font-size: 1.2rem;
        font-weight: bold;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        background-color: white;
        color: #333;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        border-color: #4CAF50;
        color: #4CAF50;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1 class="main-title">HealMate AI 🩺</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">你的专属健康陪伴者，接纳一切不完美，慢慢来。</p>', unsafe_allow_html=True)

# 检查连续未打卡提醒
last_checkin = get_last_checkin_date()
if last_checkin and st.session_state.get("profile_complete"):
    last_date = datetime.strptime(last_checkin, "%Y-%m-%d").date()
    today_date = datetime.now().date()
    if (today_date - last_date).days >= 2:
        st.info("💚 我注意到你最近没打卡，是遇到困难了吗？没关系，休息一下，随时可以重新开始。需要调整目标的话，可以在咨询页面修改信息。")

st.markdown("---")
st.write("### 请选择你要进行的操作：")

col1, col2 = st.columns(2)

with col1:
    if st.button("💬 去进行 AI 咨询\n\n(更新信息 / 生成方案)", use_container_width=True):
        st.switch_page("pages/1_consultation.py")

with col2:
    if st.button("✅ 去完成今日打卡\n\n(记录进度 / 获取鼓励)", use_container_width=True):
        st.switch_page("pages/2_checkin.py")

st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("提示：初次使用请先点击「AI 咨询」生成专属你的健康方案。")
