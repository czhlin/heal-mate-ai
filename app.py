import streamlit as st
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

# 配置 DeepSeek API
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# 设置页面配置
st.set_page_config(page_title="AI健康管家", layout="centered")

# 添加自定义 CSS 优化界面
st.markdown("""
    <style>
    /* 调整主标题大小 */
    .main-title {
        font-size: 3rem !important;
        font-weight: 700;
        color: #0E1117;
        margin-bottom: 1rem;
    }
    /* 表单输入框标签字体变大 */
    .stNumberInput label, .stSelectbox label {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
    }
    /* 优化表单容器 */
    [data-testid="stForm"] {
        border: 2px solid #f0f2f6;
        border-radius: 15px;
        padding: 2rem;
        background-color: #ffffff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    /* 按钮样式优化 */
    .stButton button {
        width: 100%;
        border-radius: 10px;
        height: 3rem;
        font-size: 1.1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.header("📖 使用说明")
    st.markdown("""
    1. **填写信息**：在右侧表单输入您的基本体质数据。
    2. **设定目标**：选择您希望达到的健康目标。
    3. **生成方案**：点击“生成健康方案”按钮，AI 将为您定制计划。
    4. **保存结果**：您可以查看生成的方案并点击复制按钮保存。
    """)
    
    st.markdown("---")
    st.header("⚠️ 免责声明")
    st.info("""
    本应用生成的所有内容仅供参考，不构成医疗建议、诊断或治疗方案。
    在开始任何新的饮食或运动计划之前，请务必咨询专业医生的意见。
    """)

def save_to_history(input_data, output_text):
    """
    将用户输入和方案保存到本地 JSON 文件
    """
    history_file = "history.json"
    
    # 构造单条记录
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input": input_data,
        "output": output_text
    }
    
    # 读取现有记录
    history_list = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history_list = json.load(f)
        except (json.JSONDecodeError, IOError):
            history_list = []
            
    # 追加新记录
    history_list.append(record)
    
    # 保存回文件
    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history_list, f, ensure_ascii=False, indent=4)
    except IOError as e:
        st.error(f"保存历史记录失败: {str(e)}")

def generate_plan(height, weight, age, gender, goal, diet):
    """
    调用 DeepSeek API 生成个性化健康方案
    """
    prompt = f"""你是一位专业的营养师。根据以下用户信息生成个性化健康方案，包括饮食建议、饮水目标、睡眠建议和运动建议。请用分段形式，每段开头用【饮食】【饮水】【睡眠】【运动】标注。

用户信息：
- 身高：{height} cm
- 体重：{weight} kg
- 年龄：{age} 岁
- 性别：{gender}
- 健康目标：{goal}
- 饮食方式：{diet}

要求：
1. 饮食要具体到食材（考虑用户饮食方式）。
2. 饮水用杯数表达。
3. 睡眠给具体时间。
4. 运动给具体动作或时长。
5. 最后加一句鼓励的话。
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的健康管理专家。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"API 调用失败: {str(e)}")

# 主页面标题
st.markdown('<h1 class="main-title">AI健康管家 🩺</h1>', unsafe_allow_html=True)
st.markdown("---")

# 创建表单
with st.form("health_info_form"):
    st.subheader("请输入您的基本信息")
    
    col1, col2 = st.columns(2)
    with col1:
        height = st.number_input("身高 (cm)", min_value=50, max_value=250, value=170, step=1)
        age = st.number_input("年龄", min_value=1, max_value=120, value=25, step=1)
    with col2:
        weight = st.number_input("体重 (kg)", min_value=10.0, max_value=300.0, value=65.0, step=0.1)
        gender = st.selectbox("性别", options=["男", "女"])

    st.markdown("---")
    st.subheader("生活习惯与目标")
    
    health_goal = st.selectbox("健康目标", options=["减肥", "增肌", "保持健康"])
    diet_style = st.selectbox("饮食方式", options=["自己做饭", "外卖为主", "混合"])
    
    # 提交按钮
    submitted = st.form_submit_button("生成健康方案")

# 表单提交后的处理逻辑
if submitted:
    # 显示正在生成的提示
    with st.status("正在生成方案...", expanded=True) as status:
        try:
            st.write("正在分析您的体质数据并连接 AI...")
            # 调用 API
            plan = generate_plan(height, weight, age, gender, health_goal, diet_style)
            
            # 保存到历史记录
            user_input = {
                "height": height,
                "weight": weight,
                "age": age,
                "gender": gender,
                "goal": health_goal,
                "diet": diet_style
            }
            save_to_history(user_input, plan)
            
            status.update(label="方案生成完毕！", state="complete", expanded=False)
            
            # 显示结果
            st.success("您的个性化健康方案已生成并已存入历史记录：")
            
            # 使用 st.markdown 展示美化后的结果
            st.markdown(plan)
            
            st.markdown("---")
            # 复制功能：使用 st.code 展示结果，Streamlit 自带复制按钮
            st.subheader("📋 方案文本（可点击右上角图标复制）")
            st.code(plan, language="markdown")
            
            st.info("💡 提示：以上方案由 AI 生成，请结合自身实际情况参考。")
            
        except Exception as e:
            status.update(label="生成失败", state="error", expanded=False)
            st.error(f"抱歉，生成方案时遇到了问题：{str(e)}")
            st.warning("请检查您的 API Key 是否正确配置，或稍后再试。")
