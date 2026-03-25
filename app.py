import streamlit as st

# ==========================================
# 统一设置页面配置（必须在主入口最上方）
# ==========================================
st.set_page_config(page_title="HealMate AI 健康管家", layout="centered", page_icon="🩺")

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
