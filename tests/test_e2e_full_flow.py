import os
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
def test_e2e_full_flow_consultation_plan_checkin_dashboard():
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
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded")

            page.get_by_label("专属昵称 / 账号").fill("e2e_user_full")
            page.get_by_label("密码（新用户将自动注册）").fill("e2e_password")
            page.get_by_role("button", name="登录 / 注册").click()
            page.get_by_text("当前用户").wait_for(timeout=30000)

            page.get_by_text("AI 咨询").click()
            page.get_by_text("💬 AI健康管家").wait_for(timeout=30000)

            chat = page.get_by_placeholder("输入你的回答...")
            chat.fill("170cm, 69kg, 27岁, 男")
            chat.press("Enter")
            page.get_by_text("健康目标").wait_for(timeout=30000)

            chat = page.get_by_placeholder("输入你的回答...")
            chat.fill("减脂")
            chat.press("Enter")
            page.get_by_text("饮食方式").wait_for(timeout=30000)

            chat = page.get_by_placeholder("输入你的回答...")
            chat.fill("外卖为主")
            chat.press("Enter")
            page.get_by_text("过敏").wait_for(timeout=30000)

            chat = page.get_by_placeholder("输入你的回答...")
            chat.fill("没有")
            chat.press("Enter")
            page.get_by_text("买菜").wait_for(timeout=30000)

            chat = page.get_by_placeholder("输入你的回答...")
            chat.fill("超市")
            chat.press("Enter")
            page.get_by_text("厨具").wait_for(timeout=30000)

            chat = page.get_by_placeholder("输入你的回答...")
            chat.fill("电饭煲")
            chat.press("Enter")
            page.get_by_text("多少时间做饭").wait_for(timeout=30000)

            chat = page.get_by_placeholder("输入你的回答...")
            chat.fill("20分钟")
            chat.press("Enter")

            page.get_by_text("选择方案版本").wait_for(timeout=30000)
            page.get_by_text("我想要理想版").click()
            page.get_by_text("当前版本").wait_for(timeout=30000)

            page.get_by_text("今日打卡").click()
            page.get_by_text("✅ 今日打卡").wait_for(timeout=30000)

            page.get_by_text("编辑我的打卡任务").click()
            page.get_by_label("每行一个任务").fill("喝水 2000ml\n晚上 23:30 睡觉\n散步 20分钟\n拉伸 5分钟")
            page.get_by_text("保存任务").click()
            page.get_by_text("已更新打卡任务").wait_for(timeout=30000)

            page.get_by_text("拉伸 5分钟").wait_for(timeout=30000)
            page.get_by_text("拉伸 5分钟").click()
            page.get_by_label("今天感觉怎么样？（选填，比如：太累了不想动）").fill("今天还行")
            page.get_by_role("button", name="🚀 提交今日打卡").click()
            page.get_by_text("打卡成功").wait_for(timeout=30000)

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
