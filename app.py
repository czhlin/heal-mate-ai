import time
import streamlit as st
from database import init_db, create_session, delete_session, get_user_id_by_session, verify_or_create_user

st.set_page_config(page_title="HealMate AI 健康管家", layout="centered", page_icon="🩺")

init_db()

def hide_streamlit_ui():
    st.markdown(
        """
        <style>
        #MainMenu { display: none; }
        footer { display: none; }
        [data-testid="stToolbar"] { display: none; }
        [data-testid="stToolbarActions"] { display: none; }
        [data-testid="stDeployButton"] { display: none; }
        [data-testid="stDecoration"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def apply_theme(theme: str):
    if theme == "dark":
        st.markdown(
            """
            <style>
            :root {
              --hm-bg: #0E1117;
              --hm-bg2: #0B0F14;
              --hm-text: #FAFAFA;
              --hm-muted: rgba(250,250,250,0.72);
              --hm-card: #161B22;
              --hm-border: rgba(250,250,250,0.14);
              --hm-input: #0B1220;
              --hm-input-text: #FAFAFA;
              --hm-placeholder: rgba(250,250,250,0.48);
              --hm-primary: #4CAF50;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            :root {
              --hm-bg: #FFFFFF;
              --hm-bg2: #F6F7F9;
              --hm-text: #0E1117;
              --hm-muted: rgba(14,17,23,0.72);
              --hm-card: #FFFFFF;
              --hm-border: rgba(14,17,23,0.12);
              --hm-input: #FFFFFF;
              --hm-input-text: #0E1117;
              --hm-placeholder: rgba(14,17,23,0.40);
              --hm-primary: #2E7D32;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <style>
        .stApp { color: var(--hm-text); }
        [data-testid="stAppViewContainer"] { background-color: var(--hm-bg); }
        [data-testid="stSidebarContent"] { background-color: var(--hm-bg2); }
        [data-testid="stSidebar"] { border-right: 1px solid var(--hm-border); }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stBottomBlockContainer"] { background: var(--hm-bg); border-top: 1px solid var(--hm-border); }

        .stApp, .stApp p, .stApp span, .stApp label, .stApp li,
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
          color: var(--hm-text);
        }
        .stApp small, .stApp .stCaption, .stApp [data-testid="stCaptionContainer"] {
          color: var(--hm-muted);
        }

        [data-testid="stChatMessage"] { background: transparent; }

        div[data-baseweb="input"] input,
        div[data-baseweb="textarea"] textarea {
          background-color: var(--hm-input) !important;
          color: var(--hm-input-text) !important;
          border-color: var(--hm-border) !important;
        }
        div[data-baseweb="input"] input::placeholder,
        div[data-baseweb="textarea"] textarea::placeholder {
          color: var(--hm-placeholder) !important;
        }
        div[data-baseweb="select"] > div {
          background-color: var(--hm-input) !important;
          border-color: var(--hm-border) !important;
        }
        div[data-baseweb="select"] * {
          color: var(--hm-input-text) !important;
        }

        details, summary {
          border-color: var(--hm-border) !important;
        }
        details > summary {
          background: var(--hm-card) !important;
        }
        details > div {
          background: transparent !important;
        }

        div.stButton > button:first-child {
          border-color: var(--hm-border) !important;
          background-color: var(--hm-card) !important;
          color: var(--hm-text) !important;
        }
        div.stButton > button:first-child:hover {
          border-color: var(--hm-primary) !important;
          color: var(--hm-primary) !important;
        }

        [data-testid="stChatInput"] { background: transparent !important; }
        [data-testid="stChatInput"] > div { background: transparent !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

# 使用 Streamlit 官方提供的纯前端 JS 注入方式写入 Cookie，抛弃各种不稳定且存在 iframe 跨域/线上安全限制的第三方库
def set_cookie(name: str, value: str, max_age: int = 30*86400):
    # SameSite=Lax 保证在普通导航和刷新时能正确带上 Cookie
    js = f"document.cookie = '{name}={value}; max-age={max_age}; path=/; SameSite=Lax';"
    st.components.v1.html(f"<script>{js}</script>", height=0)

def remove_cookie(name: str):
    js = f"document.cookie = '{name}=; max-age=0; path=/; SameSite=Lax';"
    st.components.v1.html(f"<script>{js}</script>", height=0)

def hide_sidebar():
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )

hide_streamlit_ui()

if "theme" not in st.session_state:
    cookies = getattr(st, "context", None)
    theme_cookie = cookies.cookies.get("healmate_theme") if (cookies and hasattr(cookies, "cookies")) else None
    st.session_state.theme = theme_cookie if theme_cookie in ("light", "dark") else "light"

apply_theme(st.session_state.get("theme") or "light")

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

if "user_id" not in st.session_state or not st.session_state.user_id:
    hide_sidebar()
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
                    set_cookie("healmate_session", session_token, max_age=30*86400) # 保存30天
                    st.success("登录成功，请等待跳转...")
                    time.sleep(1) # 稍微停顿一下给用户看成功提示，顺便给组件渲染时间
                    st.rerun()
                else:
                    st.error("密码错误！如果你是新用户，请换一个尚未被注册的账号名。")
    
    if "user_id" not in st.session_state or not st.session_state.user_id:
        st.stop()

with st.sidebar:
    st.markdown(f"👤 当前用户: **{st.session_state.user_id}**")
    theme = st.session_state.get("theme") or "light"
    theme_button = "🌙 切换深色" if theme == "light" else "☀️ 切换浅色"
    if st.button(theme_button, use_container_width=True):
        st.session_state.theme = "dark" if theme == "light" else "light"
        set_cookie("healmate_theme", st.session_state.theme, max_age=365*86400)
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

home_page = st.Page("views/home.py", title="首页", icon="🏠", default=True)
consultation_page = st.Page("views/1_consultation.py", title="AI 咨询", icon="💬")
checkin_page = st.Page("views/2_checkin.py", title="今日打卡", icon="✅")

# 挂载路由和侧边栏
pg = st.navigation({
    "导航": [home_page, consultation_page, checkin_page]
})

pg.run()
