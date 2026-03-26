import json

from config import DEEPSEEK_API_KEY, PLAN_VERSIONS
from openai import OpenAI

# 配置 DeepSeek API 客户端
client = OpenAI(
    api_key=DEEPSEEK_API_KEY if DEEPSEEK_API_KEY else "dummy_key",
    base_url="https://api.deepseek.com",
)


def generate_plan(user_data, version_key):
    version_req = PLAN_VERSIONS.get(version_key, PLAN_VERSIONS["ideal"])["requirements"]

    prompt = f"""你是一位充满同理心、专业的AI健康管家。根据以下用户的详细信息生成高度个性化的健康方案。
请用分段形式，每段开头用【饮食】【饮水】【睡眠】【运动】标注。

【用户信息】
- 基本身体数据：{user_data.get("basic_info", "未提供")}
- 健康目标：{user_data.get("goal", "未提供")}
- 饮食方式：{user_data.get("diet", "未提供")}
- 过敏/不耐受：{user_data.get("allergies", "无")}
- 买菜渠道：{user_data.get("grocery", "未提供")}
- 现有厨具：{user_data.get("kitchenware", "未提供")}
- 做饭时间：{user_data.get("cooking_time", "未提供")}

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
            stream=False,
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"API 调用失败: {str(e)}") from e


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
            stream=False,
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
            stream=False,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return f"打卡成功！已完成 {completed_count}/{total_count} 项，继续加油哦！"


def generate_checkin_reply(feedback: str, completed_tasks: list, total_tasks_count: int) -> str:
    """
    根据用户的打卡反馈生成温暖的 AI 回应
    """
    prompt = f"""
    你是一个极其温柔、有同理心的 AI 健康管家。
    今天用户的打卡情况如下：
    - 完成了 {len(completed_tasks)}/{total_tasks_count} 个任务。
    - 用户的感受反馈："{feedback}"

    请根据用户的反馈，写一段简短（50-100字）、积极、温暖、充满力量的回复。
    如果用户感到疲惫、沮丧，请接纳他们的情绪并给予安慰，告诉他们休息也没关系；
    如果用户感到开心、有成就感，请给予真诚的赞美和鼓励。
    不需要给出长篇大论的建议，重点是情感陪伴。
    """

    response = client.chat.completions.create(
        model="deepseek-chat", messages=[{"role": "system", "content": prompt}], temperature=0.7
    )

    return response.choices[0].message.content.strip()
