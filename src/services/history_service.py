import json
import os
from datetime import datetime

from config import HISTORY_PATH


def save_to_history(input_data, output_text, user_id="default"):
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_id,
        "input": input_data,
        "output": output_text,
    }
    history_list = []
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                history_list = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    history_list.append(record)
    try:
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history_list, f, ensure_ascii=False, indent=4)
    except IOError:
        pass
