import os
import json
from datetime import datetime

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