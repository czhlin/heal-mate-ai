import time
import streamlit as st
from database import init_db, create_session, delete_session, get_user_id_by_session, verify_or_create_user
from streamlit_cookies_controller import CookieController, RemoveEmptyElementContainer

st.set_page_config(page_title="HealMate AI 健康管家", layout="centered", page_icon="🩺")

init_db()

controller = CookieController()
RemoveEmptyElementContainer()

if "cookie_checked" not in st.session_state:
    st.session_state.cookie_checked = False

def safe_get_cookie(name: str):
    try:
        return controller.get(name)
    except TypeError:
        return None

if "user_id" not in st.session_state or not st.session_state.user_id:
    token = safe_get_cookie("healmate_session")
    if token:
        user_id = get_user_id_by_session(token)
        if user_id:
            st.session_state.user_id = user_id
            st.session_state.cookie_checked = True

if "user_id" not in st.session_state or not st.session_state.user_id:
    if not st.session_state.cookie_checked:
        st.session_state.cookie_checked = True
        st.markdown("<h3 style='text-align: center; margin-top: 50px;'>⏳ 正在验证身份信息，请稍候...</h3>", unsafe_allow_html=True)
        time.sleep(0.5)
        st.rerun()
        
    st.title("👋 欢迎来到 HealMate AI")
    st.markdown("为了保证你的数据隐私和定制化体验，请输入你的账号和密码：")
    
    with st.form("login_form"):
        username = st.text_input("专属昵称 / 账号")
        password = st.text_input("密码（新用户将自动注册）", type="password")
        submitted = st.form_submit_button("登录 / 注册", use_container_width=True)
        if submitted:
            if not username.strip() or not password.strip():
                st.error("账号和密码不能为空哦！")
            else:
                if verify_or_create_user(username.strip(), password.strip()):
                    user_id = username.strip()
                    st.session_state.user_id = user_id
                    session_token = create_session(user_id)
                    controller.set("healmate_session", session_token, max_age=30*86400)
                    st.success("登录成功，请等待跳转...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("密码错误！如果你是新用户，请换一个尚未被注册的账号名。")
    
    if "user_id" not in st.session_state or not st.session_state.user_id:
        st.stop()

with st.sidebar:
    st.markdown(f"👤 当前用户: **{st.session_state.user_id}**")
    if st.button("退出登录"):
        token = safe_get_cookie("healmate_session")
        if token:
            delete_session(token)
            controller.remove("healmate_session")
            time.sleep(0.5)
        st.session_state.clear()
        st.rerun()
    st.markdown("---")

home_page = st.Page("views/home.py", title="首页", icon="🏠", default=True)
consultation_page = st.Page("views/1_consultation.py", title="AI 咨询", icon="💬")
checkin_page = st.Page("views/2_checkin.py", title="今日打卡", icon="✅")

# 挂载路由和侧边栏
pg = st.navigation({
    "导航": [home_page, consultation_page, checkin_page]
})

pg.run()
