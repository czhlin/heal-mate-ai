import streamlit as st
from datetime import datetime
from streamlit.errors import StreamlitAPIException
from database import init_db, get_last_checkin_date, load_latest_plan, load_latest_user_profile, save_user_profile
from config import PLAN_VERSIONS
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

latest_plan = load_latest_plan()
if latest_plan:
    version = PLAN_VERSIONS.get(latest_plan["version_key"]) or PLAN_VERSIONS["ideal"]
    with st.expander(f"📌 当前健康计划（{version['label']} · {latest_plan['created_at']}）", expanded=True):
        st.markdown(latest_plan["plan_text"])
else:
    st.info("还没有生成过健康计划。先去 AI 咨询生成一份吧。")

# 快速调整入口
with st.expander("⚙️ 快速调整（可选）", expanded=False):
    latest_profile = load_latest_user_profile() or st.session_state.get("user_data") or {}
    c1, c2 = st.columns(2)
    with c1:
        goal = st.text_input("健康目标", value=(latest_profile.get("goal") or ""))
        diet = st.text_input("饮食方式", value=(latest_profile.get("diet") or ""))
        cooking_time = st.text_input("做饭时间", value=(latest_profile.get("cooking_time") or ""))
    with c2:
        allergies = st.text_input("过敏/不耐受", value=(latest_profile.get("allergies") or ""))
        grocery = st.text_input("买菜渠道", value=(latest_profile.get("grocery") or ""))
        kitchenware = st.text_input("现有厨具", value=(latest_profile.get("kitchenware") or ""))

    selected_version = st.selectbox(
        "要用哪个版本重新生成？",
        options=list(PLAN_VERSIONS.keys()),
        format_func=lambda k: PLAN_VERSIONS[k]["label"],
        index=(list(PLAN_VERSIONS.keys()).index(latest_plan["version_key"]) if latest_plan else 0),
    )

    if st.button("保存调整并去重新生成方案", use_container_width=True):
        new_profile = {
            "basic_info": latest_profile.get("basic_info") or st.session_state.get("user_data", {}).get("basic_info") or "",
            "goal": goal,
            "diet": diet,
            "allergies": allergies,
            "grocery": grocery,
            "kitchenware": kitchenware,
            "cooking_time": cooking_time,
        }
        save_user_profile(new_profile)
        st.session_state.user_data = new_profile
        st.session_state.profile_complete = True
        st.session_state.editing = False
        st.session_state.selected_plan_version = selected_version
        st.session_state.generating_plan = True
        safe_switch_page("pages/1_consultation.py")

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

def safe_switch_page(page_path):
    try:
        st.switch_page(page_path)
    except StreamlitAPIException:
        st.error("页面未加载成功。请停止并重新启动 Streamlit 应用后再试一次。")

with col1:
    if st.button("💬 去进行 AI 咨询\n\n(更新信息 / 生成方案)", use_container_width=True):
        safe_switch_page("pages/1_consultation.py")

with col2:
    if st.button("✅ 去完成今日打卡\n\n(记录进度 / 获取鼓励)", use_container_width=True):
        safe_switch_page("pages/2_checkin.py")

st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("提示：初次使用请先点击「AI 咨询」生成专属你的健康方案。")
