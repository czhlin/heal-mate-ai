import streamlit as st
import os
import json
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import time

# 加载环境变量
load_dotenv()

# 配置 DeepSeek API
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    api_key = "dummy_key"

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com",
)

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

# 定义对话步骤和问题
QUESTIONS = [
    {
        "key": "basic_info",
        "question": "你好，我是你的AI健康管家。我想先了解一下你的基本情况，可以吗？\n\n请告诉我你的**身高、体重、年龄和性别**。（例如：170cm, 65kg, 25岁, 男）",
        "reply": "收到！了解了你的基本身体数据。"
    },
    {
        "key": "goal",
        "question": "接下来，你的**健康目标**是什么呢？（例如：减肥 / 增肌 / 保持健康）",
        "reply": "好的，目标很明确！我会牢记在心。"
    },
    {
        "key": "diet",
        "question": "你平时的**饮食方式**是怎样的？（例如：自己做饭 / 外卖为主 / 混合）",
        "reply": "明白了，这决定了我们后续的饮食建议方向。"
    },
    {
        "key": "allergies",
        "question": "安全第一！你有任何**食物过敏或不耐受**吗？（例如：乳糖不耐受 / 对花生过敏 / 没有）",
        "reply": "已记录。我会避开这些让你不舒服的食物。"
    },
    {
        "key": "grocery",
        "question": "你平时主要在**哪里买菜**呢？（例如：大型超市 / 菜市场 / 线上买菜平台）",
        "reply": "这很有用，这样我推荐的食材你会更容易买到。"
    },
    {
        "key": "kitchenware",
        "question": "你**家里有什么厨具**呢？（例如：只有电饭煲 / 有空气炸锅和微波炉 / 厨具齐全）",
        "reply": "太棒了，我会根据你的厨具来设计食谱。"
    },
    {
        "key": "cooking_time",
        "question": "最后一个问题：你每天能抽出**多少时间做饭**？（例如：只有20分钟 / 周末才有空 / 每天1小时）",
        "reply": "感谢你的分享！所有信息已收集完毕。"
    }
]

DB_PATH = os.getenv("HEALMATE_DB_PATH", "healmate.db")

PLAN_VERSIONS = {
    "ideal": {
        "label": "理想版",
        "button": "我想要理想版",
        "hint": "适合有时间做饭",
        "requirements": "理想版：给出详细食谱，务必考虑用户的买菜渠道与厨具，并按一天的时间线安排。",
    },
    "lazy": {
        "label": "懒人版",
        "button": "我想要懒人版",
        "hint": "没时间，用补充剂兜底",
        "requirements": "懒人版：以便利店/外卖为核心给出可执行选择，并提供基础补充剂建议（如复合维生素、蛋白粉），同时给出最小行动清单。",
    },
    "free": {
        "label": "零成本版",
        "button": "我想要零成本版",
        "hint": "不额外花钱",
        "requirements": "零成本版：只利用现有条件，不推荐任何购买；优先公司饮水、走路运动、食堂免费汤等可得资源，给出不花钱的替代方案。",
    },
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                basic_info TEXT,
                goal TEXT,
                diet TEXT,
                allergies TEXT,
                grocery TEXT,
                kitchenware TEXT,
                cooking_time TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                tasks_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS check_ins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_date TEXT NOT NULL UNIQUE,
                completed_tasks_json TEXT NOT NULL,
                feedback TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

def save_user_profile(user_data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            INSERT INTO users (
                created_at, updated_at, basic_info, goal, diet, allergies, grocery, kitchenware, cooking_time
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now,
                now,
                user_data.get("basic_info"),
                user_data.get("goal"),
                user_data.get("diet"),
                user_data.get("allergies"),
                user_data.get("grocery"),
                user_data.get("kitchenware"),
                user_data.get("cooking_time"),
            ),
        )
        conn.commit()
    finally:
        conn.close()

def load_latest_user_profile():
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            """
            SELECT basic_info, goal, diet, allergies, grocery, kitchenware, cooking_time
            FROM users
            ORDER BY id DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "basic_info": row[0] or "",
            "goal": row[1] or "",
            "diet": row[2] or "",
            "allergies": row[3] or "",
            "grocery": row[4] or "",
            "kitchenware": row[5] or "",
            "cooking_time": row[6] or "",
        }
    finally:
        conn.close()

def clear_user_profiles():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM users")
        conn.execute("DELETE FROM daily_tasks")
        conn.execute("DELETE FROM check_ins")
        conn.commit()
    finally:
        conn.close()

def save_daily_tasks(tasks_list):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tasks_json = json.dumps(tasks_list, ensure_ascii=False)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("INSERT INTO daily_tasks (created_at, tasks_json) VALUES (?, ?)", (now, tasks_json))
        conn.commit()
    finally:
        conn.close()

def load_latest_daily_tasks():
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute("SELECT tasks_json FROM daily_tasks ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            return json.loads(row[0])
        return []
    finally:
        conn.close()

def save_checkin(check_date, completed_tasks_list, feedback=""):
    tasks_json = json.dumps(completed_tasks_list, ensure_ascii=False)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            INSERT INTO check_ins (check_date, completed_tasks_json, feedback) 
            VALUES (?, ?, ?)
            ON CONFLICT(check_date) DO UPDATE SET 
                completed_tasks_json=excluded.completed_tasks_json,
                feedback=excluded.feedback
            """,
            (check_date, tasks_json, feedback)
        )
        conn.commit()
    finally:
        conn.close()

def load_checkin(check_date):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute("SELECT completed_tasks_json, feedback FROM check_ins WHERE check_date = ?", (check_date,))
        row = cur.fetchone()
        if row:
            return json.loads(row[0]), row[1]
        return [], ""
    finally:
        conn.close()

def get_last_checkin_date():
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute("SELECT check_date FROM check_ins ORDER BY check_date DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            return row[0]
        return None
    finally:
        conn.close()

init_db()

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

def save_to_history(input_data, output_text):
    history_file = "history.json"
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input": input_data,
        "output": output_text
    }
    history_list = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history_list = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    history_list.append(record)
    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history_list, f, ensure_ascii=False, indent=4)
    except IOError as e:
        print(f"保存历史记录失败: {str(e)}")

def generate_plan(user_data, version_key):
    version_req = PLAN_VERSIONS.get(version_key, PLAN_VERSIONS["ideal"])["requirements"]
    
    prompt = f"""你是一位充满同理心、专业的AI健康管家。根据以下用户的详细信息生成高度个性化的健康方案。
请用分段形式，每段开头用【饮食】【饮水】【睡眠】【运动】标注。

【用户信息】
- 基本身体数据：{user_data.get('basic_info', '未提供')}
- 健康目标：{user_data.get('goal', '未提供')}
- 饮食方式：{user_data.get('diet', '未提供')}
- 过敏/不耐受：{user_data.get('allergies', '无')}
- 买菜渠道：{user_data.get('grocery', '未提供')}
- 现有厨具：{user_data.get('kitchenware', '未提供')}
- 做饭时间：{user_data.get('cooking_time', '未提供')}

【方案要求】
{version_req}
1. 饮水：用具体的杯数（如250ml/杯）表达目标，结合时间点提醒。
2. 睡眠：给具体的入睡和起床时间区间，以及睡前小建议。
3. 运动：结合目标，给出具体动作、时长或频次（考虑场地限制，如果是居家可以推荐徒手动作）。
4. 态度：要温暖、包容。在结尾加一段特别鼓励的话，告诉用户“慢慢来，即使中断了也没关系，重启比坚持更勇敢”。
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个温暖、专业、接纳用户一切限制的健康管家。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"API 调用失败: {str(e)}")

def extract_daily_tasks(plan_text):
    prompt = f"""请从以下健康方案中提取出 3-5 个适合每天打卡的具体任务。
要求：
1. 任务必须非常具体且可操作（例如：“喝水 2000ml”、“晚上 11:30 睡觉”、“散步 20分钟”）。
2. 只返回一个 JSON 数组，包含字符串列表，不要有其他任何说明或 markdown 格式标记。
示例：["喝水 2000ml", "晚上 11:30 睡觉", "散步 20分钟"]

健康方案：
{plan_text}
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个只输出 JSON 数组的数据提取工具。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            stream=False
        )
        content = response.choices[0].message.content.strip()
        # 简单清理可能包含的 markdown json 标记
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        return json.loads(content.strip())
    except Exception as e:
        print(f"提取任务失败: {e}")
        # 兜底返回几个基础任务
        return ["完成今日饮水目标", "按时入睡", "完成今日运动/活动"]

def generate_feedback(completed_count, total_count):
    if total_count == 0:
        return "今天也很棒，好好休息！"
    ratio = completed_count / total_count
    
    if ratio == 1:
        prompt_tone = "用户完成了今天所有的打卡任务，给予热情、兴奋的赞美！"
    elif ratio >= 0.5:
        prompt_tone = "用户完成了大部分打卡任务，给予肯定和鼓励，告诉他已经做得很好了。"
    else:
        prompt_tone = "用户只完成了少部分任务，给予温暖的安慰，告诉他“没关系，今天能做一点点就是进步，接纳偶尔的疲惫，明天我们再试”。"
        
    prompt = f"今日任务总数：{total_count}，已完成：{completed_count}。\n请根据以下要求生成一段简短（20-40字）的鼓励话术：\n{prompt_tone}"
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个温暖、接纳一切的AI健康陪伴者。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            stream=False
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"打卡成功！已完成 {completed_count}/{total_count} 项，继续加油哦！"

# 页面标题
st.markdown('<h1 class="main-title">AI健康管家 🩺</h1>', unsafe_allow_html=True)
st.markdown("---")

# 检查 API Key
if api_key == "dummy_key":
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
