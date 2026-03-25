import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据持久化目录配置
# Railway 中可通过挂载 Volume 到 /data 并设置 HEALMATE_DATA_DIR=/data 来实现持久化
DATA_DIR = os.getenv("HEALMATE_DATA_DIR", ".")
if not os.path.exists(DATA_DIR):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
    except Exception:
        pass

# 数据库路径配置
DB_PATH = os.path.join(DATA_DIR, "healmate.db")
HISTORY_PATH = os.path.join(DATA_DIR, "history.json")

# API Key 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

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

# 分层方案配置
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
    "minimum": {
        "label": "🌱 最小行动方案",
        "button": "我要最小行动方案",
        "hint": "困难期专属，仅1-2件小事",
        "requirements": "最小行动方案：用户当前处于困难期、动力不足或感到疲惫。请生成一个极其简单、门槛极低的【最小行动方案】。只需要包含 1 到 2 个最简单的日常任务（例如：每天喝一杯水，或者早睡15分钟）。不要任何复杂的食谱或运动计划，重点是让用户能轻松完成，建立自信。语气必须充满同理心、温和、接纳失败。",
    }
}

# 困难模式关键词
HARD_MODE_KEYWORDS = ["懒", "累", "没时间", "放弃", "不行", "做不到", "太难", "坚持不下去", "烦", "摆烂", "做不了"]
