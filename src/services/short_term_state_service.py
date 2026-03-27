from datetime import datetime, timedelta
from typing import Optional


def detect_short_term_state(text: str) -> Optional[dict]:
    t = (text or "").strip()
    if not t:
        return None

    patterns = [
        ("sick", ["感冒", "发烧", "咳嗽", "头疼", "头痛", "生病", "不舒服", "嗓子疼", "鼻塞", "发炎"], 3),
        ("travel", ["出差", "在路上", "旅行", "机场", "高铁", "火车", "酒店"], 3),
        ("period", ["大姨妈", "姨妈", "月经", "痛经", "例假"], 3),
        ("stress", ["崩溃", "焦虑", "压力", "难受", "抑郁", "emo", "烦"], 2),
        ("overtime", ["加班", "熬夜", "通宵", "996"], 2),
        ("sleep", ["失眠", "睡不着", "睡不醒"], 2),
    ]

    for key, kws, days in patterns:
        if any(kw in t for kw in kws):
            expires = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            note = t[:120]
            return {"state": key, "note": note, "expires_at": expires}

    return None
