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
def test_e2e_smoke_login_and_navigation(tmp_path):
    if os.getenv("RUN_E2E") != "1":
        pytest.skip("Set RUN_E2E=1 to run e2e tests")

    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        pytest.skip("playwright not installed")

    port = 8501
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

            if page.get_by_test_id("current-user-info").count() == 0:
                page.get_by_role("button", name="登录 / 注册").wait_for(timeout=30000)
                page.get_by_label("专属昵称 / 账号").fill(f"e2e_user_{int(time.time())}")
                page.get_by_label("密码（新用户将自动注册）").fill("e2e_password")
                page.get_by_role("button", name="登录 / 注册").click()

            page.get_by_test_id("current-user-info").wait_for(state="attached", timeout=60000)

            page.get_by_role("link", name="今日打卡").click()
            page.get_by_test_id("checkin-page").wait_for(state="attached", timeout=30000)

            page.get_by_role("link", name="成长看板").click()
            page.get_by_test_id("dashboard-page").wait_for(state="attached", timeout=30000)

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
