import os
import re
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request

import pytest


def _wait_http_ok(url: str, timeout_s: int = 30) -> None:
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                if resp.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for {url}")


@pytest.mark.e2e
def test_e2e_full_flow_consultation_plan_checkin_dashboard(tmp_path):
    if os.getenv("RUN_E2E") != "1":
        pytest.skip("Set RUN_E2E=1 to run e2e tests")

    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        pytest.skip("playwright not installed")

    port = 8502
    url = f"http://127.0.0.1:{port}"
    app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/app.py"))

    env = os.environ.copy()
    env["DEEPSEEK_API_KEY"] = env.get("DEEPSEEK_API_KEY") or "e2e_dummy_key"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    env["TESTING"] = "True"
    env["RUN_E2E"] = "1"
    env["HEALMATE_DATA_DIR"] = str(tmp_path)

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            app_path,
            "--server.headless=true",
            f"--server.port={port}",
            "--server.address=127.0.0.1",
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        _wait_http_ok(url, timeout_s=45)

        with sync_playwright() as p:
            headful = os.getenv("PW_HEADFUL") == "1"
            slow_mo = int(os.getenv("PW_SLOWMO") or "0")
            browser = p.chromium.launch(headless=not headful, slow_mo=slow_mo)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded")

            if page.get_by_text("当前用户").count() == 0:
                page.get_by_role("button", name="登录 / 注册").wait_for(timeout=30000)
                page.get_by_label("专属昵称 / 账号").fill(f"e2e_user_full_{int(time.time())}")
                page.get_by_label("密码（新用户将自动注册）").fill("e2e_password")
                page.get_by_role("button", name="登录 / 注册").click()
            page.get_by_text("当前用户").wait_for(timeout=60000)

            page.get_by_text("AI 咨询").click()
            page.get_by_text("💬 AI健康管家").wait_for(timeout=30000)
            page.get_by_text("请告诉我你的身高、体重").wait_for(timeout=30000)

            # 辅助函数：等待并发送聊天
            def send_chat(text):
                # 兼容不同版本的 streamlit 聊天输入框
                locator = page.locator(
                    "textarea[placeholder='输入你的回答...'], div[data-testid='stChatInput'] textarea"
                )
                # 使用 force_fill 或多次尝试避免不可见问题
                try:
                    locator.first.wait_for(state="attached", timeout=30000)
                    locator.first.fill(text, force=True)
                    locator.first.press("Enter")
                except Exception:
                    # 退化策略：直接找到 textarea
                    page.keyboard.type(text)
                    page.keyboard.press("Enter")

            send_chat("170cm, 69kg, 27岁, 男")
            page.get_by_text("健康目标").wait_for(timeout=30000)

            send_chat("减脂")
            page.get_by_text("饮食方式").wait_for(timeout=30000)

            send_chat("外卖为主")
            page.get_by_text("过敏").wait_for(timeout=30000)

            send_chat("没有")
            page.get_by_text("买菜").wait_for(timeout=30000)

            send_chat("超市")
            page.get_by_text("有什么厨具").first.wait_for(timeout=30000)

            send_chat("电饭煲")
            page.get_by_text("多少时间做饭").first.wait_for(timeout=30000)

            send_chat("20分钟")

            page.get_by_text("选择方案版本").wait_for(timeout=30000)
            page.get_by_text("我想要理想版").click()
            page.get_by_text("当前版本").wait_for(timeout=30000)

            page.get_by_text("今日打卡").click()
            page.get_by_text("✅ 今日打卡").wait_for(timeout=30000)

            page.get_by_text("编辑我的打卡任务").click()
            page.get_by_label("每行一个任务").fill("喝水 2000ml\n晚上 23:30 睡觉\n散步 20分钟\n拉伸 5分钟")
            page.get_by_text("保存任务").click()
            # 保存任务后页面会 rerun 刷新，等待关键元素再次出现以确认刷新完成
            page.get_by_text("拉伸 5分钟").first.wait_for(timeout=30000)
            page.get_by_text("拉伸 5分钟").first.click()
            page.get_by_label("今天感觉怎么样？（选填，比如：太累了不想动）").fill("今天还行")
            page.get_by_role("button", name="🚀 提交今日打卡").click()
            # 兼容：有时候打卡后提示语可能略有不同，或者包含表情，我们用正则表达式或者部分匹配
            page.get_by_text(re.compile(r"打卡|成功|做得很好了")).first.wait_for(timeout=30000)

            page.get_by_text("成长看板").click()
            page.get_by_text("📊 成长看板").wait_for(timeout=30000)
            page.get_by_text("累计打卡天数").wait_for(timeout=30000)

            browser.close()
    finally:
        if proc.poll() is None:
            try:
                proc.send_signal(signal.SIGINT)
            except Exception:
                proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()
