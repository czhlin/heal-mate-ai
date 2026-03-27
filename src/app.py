"""
主入口模块 (Application Entry Point)

从架构设计角度，此模块承担以下核心职责：
1. 全局生命周期管理：初始化数据库连接、执行必要的迁移 (init_db)。
2. 身份认证网关 (Authentication Gateway)：基于 Cookie 与 Session 的双重校验，阻断未授权访问。
3. 依赖注入与环境初始化：全局样式、主题以及 Streamlit 的 Page Config 设定。
4. 路由挂载 (Routing)：定义系统的页面导航拓扑。

为保证渲染性能与无缝的用户体验，这里采用了纯前端 JS 注入写 Cookie 与服务端原生读取的混合鉴权方案，
避免了传统第三方 Streamlit Cookie 库带来的重定向闪烁与 iframe 跨域问题。
"""

import time

import streamlit as st

from repos.migrations import init_db
from services.auth_service import create_session, delete_session, get_user_id_by_session, verify_or_create_user
from ui.test_ids import test_id
from ui.theme import apply_theme, hide_sidebar, hide_streamlit_ui, show_sidebar

# -----------------------------------------------------------------------------
# 1. 页面级全局配置
# -----------------------------------------------------------------------------
st.set_page_config(page_title="HealMate AI 健康管家", layout="centered", page_icon="🩺")

# -----------------------------------------------------------------------------
# 2. 基础设施初始化
# -----------------------------------------------------------------------------
# 确保数据库表结构在应用启动时就绪，支持平滑的自动化部署
init_db()


# -----------------------------------------------------------------------------
# 3. 底层通信：纯净的 Cookie 操作接口
# -----------------------------------------------------------------------------
# 使用 Streamlit 官方提供的纯前端 JS 注入方式写入 Cookie，抛弃各种不稳定且存在 iframe 跨域/线上安全限制的第三方库
def set_cookie(name: str, value: str, max_age: int = 30 * 86400):
    """
    通过 JS 将状态下发至客户端持久化。
    使用 SameSite=Lax 保证在普通导航和刷新时能正确带上 Cookie，这是跨页保持会话的关键。
    """
    js = f"document.cookie = '{name}={value}; max-age={max_age}; path=/; SameSite=Lax';"
    st.components.v1.html(f"<script>{js}</script>", height=0)


def remove_cookie(name: str):
    """清除客户端 Cookie，用于注销流程"""
    js = f"document.cookie = '{name}=; max-age=0; path=/; SameSite=Lax';"
    st.components.v1.html(f"<script>{js}</script>", height=0)


# -----------------------------------------------------------------------------
# 4. 视图层预处理 (UI Pre-processing)
# -----------------------------------------------------------------------------
hide_streamlit_ui()

if "theme" not in st.session_state:
    cookies = getattr(st, "context", None)
    theme_cookie = cookies.cookies.get("healmate_theme") if (cookies and hasattr(cookies, "cookies")) else None
    st.session_state.theme = theme_cookie if theme_cookie in ("light", "dark") else "light"

apply_theme(st.session_state.get("theme") or "light")

# -----------------------------------------------------------------------------
# 5. 路由注册 (Route Registration)
# -----------------------------------------------------------------------------
home_page = st.Page("pages/home.py", title="首页", icon="🏠", default=True)
consultation_page = st.Page("pages/1_consultation.py", title="AI 咨询", icon="💬")
checkin_page = st.Page("pages/2_checkin.py", title="今日打卡", icon="✅")
dashboard_page = st.Page("pages/3_dashboard.py", title="成长看板", icon="📊")

# -----------------------------------------------------------------------------
# 6. 鉴权网关与会话恢复 (Authentication & Session Recovery)
# -----------------------------------------------------------------------------
# 核心：使用 Streamlit 官方原生的 st.context.cookies 在服务端直接读取请求头里的 Cookie。
# 没有任何延迟、没有任何闪烁、不依赖 iframe！
if "user_id" not in st.session_state or not st.session_state.user_id:
    # 兼容处理：st.context 是新版本引入，如果遇到旧版可以退化
    cookies = getattr(st, "context", None)
    if cookies and hasattr(cookies, "cookies"):
        token = cookies.cookies.get("healmate_session")
    else:
        # 极低版本备用方案（由于我们没锁版本，Railway 肯定是最新版，所以基本走上面）
        token = None

    if token:
        user_id = get_user_id_by_session(token)
        if user_id:
            st.session_state.user_id = user_id

# -----------------------------------------------------------------------------
# 7. 登录视图 (Fallback Login View)
# 当鉴权网关未通过时，降级渲染登录视图，并阻断后续的路由加载
# -----------------------------------------------------------------------------
if "user_id" not in st.session_state or not st.session_state.user_id:
    hide_sidebar()
    st.title("👋 欢迎来到 HealMate AI")
    st.markdown("为了保证你的数据隐私和定制化体验，请输入你的账号和密码：")

    with st.form("login_form", enter_to_submit=False):
        username = st.text_input("专属昵称 / 账号")
        password = st.text_input("密码（新用户将自动注册）", type="password")
        submitted = st.form_submit_button("登录 / 注册", use_container_width=True)
        if submitted:
            if not username.strip() or not password.strip():
                st.error("账号和密码不能为空哦！")
            else:
                # 调用 Service 层接口进行凭证核验与会话创建
                if verify_or_create_user(username.strip(), password.strip()):
                    user_id = username.strip()
                    st.session_state.user_id = user_id
                    session_token = create_session(user_id)
                    set_cookie("healmate_session", session_token, max_age=30 * 86400)  # 保存30天
                    st.success("登录成功，请等待跳转...")
                    time.sleep(1)  # 稍微停顿一下给用户看成功提示，顺便给组件渲染时间
                    st.rerun()  # 这里直接重新运行，由下方 navigation 接管页面
                else:
                    st.error("密码错误！如果你是新用户，请换一个尚未被注册的账号名。")

    if "user_id" not in st.session_state or not st.session_state.user_id:
        st.stop()  # 硬阻断，防止继续向下执行泄露业务逻辑或报错

# -----------------------------------------------------------------------------
# 8. 授权态容器及导航挂载
# -----------------------------------------------------------------------------
show_sidebar()

with st.sidebar:
    test_id("current-user-info")
    st.markdown(f"👤 当前用户: **{st.session_state.user_id}**")
    theme = st.session_state.get("theme") or "light"
    theme_button = "🌙 切换深色" if theme == "light" else "☀️ 切换浅色"
    if st.button(theme_button, use_container_width=True):
        st.session_state.theme = "dark" if theme == "light" else "light"
        set_cookie("healmate_theme", st.session_state.theme, max_age=365 * 86400)
        time.sleep(0.2)
        st.rerun()
    if st.button("退出登录"):
        cookies = getattr(st, "context", None)
        token = cookies.cookies.get("healmate_session") if (cookies and hasattr(cookies, "cookies")) else None
        if token:
            delete_session(token)
            remove_cookie("healmate_session")
            time.sleep(0.5)
        st.session_state.clear()
        st.rerun()
    st.markdown("---")

# 挂载路由，交由 Streamlit 内置导航器接管后续的生命周期
pg = st.navigation({"导航": [home_page, consultation_page, checkin_page, dashboard_page]})

pg.run()
