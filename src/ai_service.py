import json
import os
import re

from openai import OpenAI

from config import DEEPSEEK_API_KEY, PLAN_VERSIONS

# 配置 DeepSeek API 客户端
client = OpenAI(
    api_key=DEEPSEEK_API_KEY if DEEPSEEK_API_KEY else "dummy_key",
    base_url="https://api.deepseek.com",
)


def _is_test_mode() -> bool:
    return os.getenv("TESTING") == "True" or os.getenv("RUN_E2E") == "1"


def generate_plan(user_data, version_key):
    if _is_test_mode():
        version_req = PLAN_VERSIONS.get(version_key, PLAN_VERSIONS["ideal"])["requirements"]
        basic_info = user_data.get("basic_info", "未提供")
        goal = user_data.get("goal", "未提供")
        diet = user_data.get("diet", "未提供")
        return (
            f"【饮食】根据你的饮食方式（{diet}）与目标（{goal}），优先保证蛋白质与蔬菜摄入。\n\n"
            "【饮水】目标：每日 2000ml（250ml/杯 × 8）。建议：起床 1 杯、上午 2 杯、下午 3 杯、晚间 2 杯。\n\n"
            "【睡眠】建议 23:30-00:30 入睡，7:30-8:30 起床。睡前 30 分钟减少刷屏。\n\n"
            "【运动】每周 3 次 20 分钟快走或徒手训练，按当日状态灵活调整。\n\n"
            f"（测试模式）已根据：{basic_info} 生成。版本要求：{version_req}"
        )
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
    if _is_test_mode():
        return ["喝水 2000ml", "晚上 23:30 睡觉", "散步 20分钟"]
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
    if _is_test_mode():
        if total_count == 0:
            return "今天也很棒，好好休息！"
        return f"（测试模式）已完成 {completed_count}/{total_count} 项，做得很好。"
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
    if _is_test_mode():
        completed = len(completed_tasks)
        return f"（测试模式）收到你的感受：{feedback}。今天完成 {completed}/{total_tasks_count}，已经很棒了。"
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


def _clean_json_text(content: str) -> str:
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        parts = content.split("\n", 1)
        content = parts[1] if len(parts) == 2 else content
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()


def normalize_consultation_answer(
    question_key: str,
    question_text: str,
    user_input: str,
    is_hard_mode: bool = False,
    existing_value=None,
) -> dict:
    if _is_test_mode():
        raw = (user_input or "").strip()
        existing = (existing_value or "").strip()
        negative = raw in {"不知道", "不清楚", "不确定", "随便", "不想说"}
        if negative and existing:
            return {"value": existing, "sufficient": True, "assistant_reply": "好的，保持不变。", "follow_up": ""}

        if question_key == "basic_info":
            h = re.search(r"(\d+(?:\.\d+)?)\s*(?:cm|厘米)", raw, re.IGNORECASE)
            w = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg|公斤)", raw, re.IGNORECASE)
            age = re.search(r"(\d{1,3})\s*岁", raw)
            sex = "男" if ("男" in raw and "女" not in raw) else ("女" if "女" in raw else "")
            if h and w:
                parts = [f"{h.group(1)}cm", f"{w.group(1)}kg"]
                if age:
                    parts.append(f"{age.group(1)}岁")
                if sex:
                    parts.append(sex)
                return {
                    "value": ", ".join(parts),
                    "sufficient": True,
                    "assistant_reply": "收到，已记录你的基本信息。",
                    "follow_up": "",
                }
            return {
                "value": "",
                "sufficient": False,
                "assistant_reply": "没关系，我们慢慢来。为了生成更合适的方案，我需要你的身高和体重。",
                "follow_up": "可以按这个格式告诉我：170cm, 65kg",
            }

        if negative or not raw:
            return {
                "value": "",
                "sufficient": False,
                "assistant_reply": "我理解你现在不太想回答。为了把方案做得更贴合你，我还需要这一项信息。",
                "follow_up": question_text.replace("？", "").replace("?", "").strip(),
            }

        return {"value": raw, "sufficient": True, "assistant_reply": "收到，已记录。", "follow_up": ""}

    mode_hint = "用户处于困难/疲惫状态，请更温柔、降低压力。" if is_hard_mode else "正常状态。"
    prompt = f"""
你是一位温柔、专业的健康信息采集助手。你的任务是提取用户的回答，判断是否满足当前问题的要求。你可以和用户唠嗑共情，但【绝对不要擅自提出新问题】。

当前正在收集的特定字段：{question_key}
你只能关注这个字段，【不要】去问其他字段（比如睡眠、水果等），更不要去问之前已经问过的问题！
当前系统设定的提问：{question_text}
已有值（可能为空）：{existing_value or ""}
用户最新输入：{user_input}
用户状态提示：{mode_hint}

请只输出一个 JSON 对象，不要输出任何 markdown，不要输出多余文字。JSON 字段如下：
- value: string（把用户输入转成适合写入该字段的一句话答案；如果用户没给出，保留已有值或留空）
- sufficient: boolean（判断提取到的 value 是否足以回答“当前系统设定的提问”。注意：只要用户给出了核心信息就算足够。比如 basic_info 至少要包含身高与体重）
- assistant_reply: string（1-2 句。如果 sufficient=true，只表达共情、赞美或感谢，【绝对禁止】在结尾带问号或提出任何新问题！如果 sufficient=false，先接住情绪/对话，然后解释为什么我们需要这个信息。）
- follow_up: string（只有当 sufficient=false 时才填写！给一个很短、很具体、仅针对当前字段的追问；否则必须留空字符串）

规则（必须严格遵守）：
1. 你的回答中【禁止】出现预设字段以外的医疗提问。
2. 当 sufficient=true 时，`assistant_reply` 必须是陈述句结束，绝不允许抛出任何疑问句！因为系统会自动在后面拼上下一道题。
3. 追问只问当前缺失的 1 个点，给用户一个可复制的简单回答格式。
""".strip()
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个只输出 JSON 的健康信息采集工具。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            stream=False,
        )
        content = _clean_json_text(response.choices[0].message.content)
        data = json.loads(content)
        return {
            "value": str(data.get("value") or "").strip(),
            "sufficient": bool(data.get("sufficient")),
            "assistant_reply": str(data.get("assistant_reply") or "").strip(),
            "follow_up": str(data.get("follow_up") or "").strip(),
        }
    except Exception:
        return {
            "value": user_input.strip(),
            "sufficient": True,
            "assistant_reply": "",
            "follow_up": "",
        }
