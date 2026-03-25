import streamlit as st
from database import init_db

# ==========================================
# 统一设置页面配置（必须在主入口最上方）
# ==========================================
st.set_page_config(page_title="HealMate AI 健康管家", layout="centered", page_icon="🩺")

# 初始化数据库结构
init_db()

# ==========================================
# 简单的多用户登录拦截
# ==========================================
if "user_id" not in st.session_state or not st.session_state.user_id:
    st.title("👋 欢迎来到 HealMate AI")
    st.markdown("为了保证你的数据隐私和定制化体验，请输入你的专属昵称或账号：")
    
    with st.form("login_form"):
        username = st.text_input("专属昵称 / 账号（请记住它以便下次登录）")
        submitted = st.form_submit_button("进入系统", use_container_width=True)
        if submitted:
            if username.strip():
                st.session_state.user_id = username.strip()
                st.rerun()
            else:
                st.error("昵称不能为空哦！")
    st.stop()

# 侧边栏显示当前用户并提供退出选项
with st.sidebar:
    st.markdown(f"👤 当前用户: **{st.session_state.user_id}**")
    if st.button("退出登录"):
        st.session_state.clear()
        st.rerun()
    st.markdown("---")

# ==========================================
# 定义页面路由 (使用 Streamlit >= 1.36 的 st.navigation)
# ==========================================
# 注意：文件路径使用相对路径，这里我们用英文文件名，但侧边栏显示由 title 控制
home_page = st.Page("views/home.py", title="首页", icon="🏠", default=True)
consultation_page = st.Page("views/1_consultation.py", title="AI 咨询", icon="💬")
checkin_page = st.Page("views/2_checkin.py", title="今日打卡", icon="✅")

# 挂载路由和侧边栏
pg = st.navigation({
    "导航": [home_page, consultation_page, checkin_page]
})

# 运行当前选中的页面
pg.run()
