import time
import streamlit as st
from database import init_db, create_session, delete_session, get_user_id_by_session, verify_or_create_user
from streamlit_cookies_controller import CookieController, RemoveEmptyElementContainer

# ==========================================
# 统一设置页面配置（必须在主入口最上方）
# ==========================================
st.set_page_config(page_title="HealMate AI 健康管家", layout="centered", page_icon="🩺")

# 初始化数据库结构
init_db()

controller = CookieController()
RemoveEmptyElementContainer()

# 尝试从 cookie 恢复会话（如果当前 session_state 中没有 user_id）
if "user_id" not in st.session_state or not st.session_state.user_id:
    token = controller.get("healmate_session")
    if token:
        user_id = get_user_id_by_session(token)
        if user_id:
            st.session_state.user_id = user_id

# ==========================================
# 简单的多用户登录拦截
# ==========================================
if "user_id" not in st.session_state or not st.session_state.user_id:
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
                    controller.set("healmate_session", session_token, max_age=30*86400) # 保存30天
                    st.success("登录成功，请等待跳转...")
                    time.sleep(1) # 稍微停顿一下给用户看成功提示，顺便给组件渲染时间
                    st.rerun()
                else:
                    st.error("密码错误！如果你是新用户，请换一个尚未被注册的账号名。")
    
    # 只有确实未登录才停止后续渲染
    if "user_id" not in st.session_state or not st.session_state.user_id:
        st.stop()

# 侧边栏显示当前用户并提供退出选项
with st.sidebar:
    st.markdown(f"👤 当前用户: **{st.session_state.user_id}**")
    if st.button("退出登录"):
        token = controller.get("healmate_session")
        if token:
            delete_session(token)
            controller.remove("healmate_session")
            # 同样给予前端时间删除 Cookie
            time.sleep(0.5)
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
