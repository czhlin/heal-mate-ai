from datetime import datetime, timedelta
from datetime import time as dt_time
from typing import Optional

import streamlit as st

from core.state import ensure_user_state
from services.checkin_service import get_all_checkins
from services.user_state_service import get_active_short_term_state

user_id = st.session_state.user_id

ensure_user_state(user_id)

st.title("📊 成长看板")
st.markdown("---")

records = get_all_checkins(user_id)
records_by_date = {r["date"]: r for r in records}

today = datetime.now().date()
end = today
start = end - timedelta(days=83)
start = start - timedelta(days=start.weekday())

dates = []
d = start
while d <= end:
    dates.append(d)
    d += timedelta(days=1)


def _intensity(rec: Optional[dict]) -> int:
    if not rec:
        return 0
    completed = len(rec.get("tasks") or [])
    total = rec.get("tasks_total_count")
    if total is None:
        snapshot = rec.get("tasks_snapshot") or []
        total = len(snapshot) if snapshot else None
    if not total:
        return 2 if completed > 0 else 1
    ratio = completed / max(1, int(total))
    if ratio >= 0.95:
        return 4
    if ratio >= 0.6:
        return 3
    if ratio > 0:
        return 2
    return 1


active_state = get_active_short_term_state(user_id)
if active_state:
    st.info(f"最近状态：{active_state.get('note')}")

st.subheader("📅 打卡热力图（近 12 周）")

color_map = {
    0: "#ebedf0",
    1: "#c6e48b",
    2: "#7bc96f",
    3: "#239a3b",
    4: "#196127",
}

cells = []
for dt in dates:
    date_str = dt.strftime("%Y-%m-%d")
    rec = records_by_date.get(date_str)
    level = _intensity(rec)
    completed = len((rec or {}).get("tasks") or [])
    total = (rec or {}).get("tasks_total_count")
    title = date_str
    if total is not None:
        title = f"{date_str} · {completed}/{total}"
    elif rec:
        title = f"{date_str} · 完成 {completed} 项"
    cells.append({"date": date_str, "level": level, "title": title})

weeks = []
week = []
for i, c in enumerate(cells):
    week.append(c)
    if (i + 1) % 7 == 0:
        weeks.append(week)
        week = []

grid_html = "<div class='heatmap'>"
for w in weeks:
    grid_html += "<div class='col'>"
    for c in w:
        grid_html += f"<div class='cell' title='{c['title']}' style='background:{color_map[c['level']]}'></div>"
    grid_html += "</div>"
grid_html += "</div>"

st.markdown(
    """
<style>
.heatmap { display:flex; gap:4px; align-items:flex-start; }
.col { display:flex; flex-direction:column; gap:4px; }
.cell { width:12px; height:12px; border-radius:2px; }
</style>
""",
    unsafe_allow_html=True,
)
st.markdown(grid_html, unsafe_allow_html=True)

st.markdown("---")
st.subheader("📈 统计")

total_days = len(records_by_date)
last_7 = 0
for i in range(7):
    ds = (today - timedelta(days=i)).strftime("%Y-%m-%d")
    if ds in records_by_date:
        last_7 += 1

streak = 0
for i in range(365):
    ds = (today - timedelta(days=i)).strftime("%Y-%m-%d")
    if ds in records_by_date:
        streak += 1
    else:
        break

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("累计打卡天数", total_days)
with c2:
    st.metric("近 7 天打卡", f"{last_7}/7")
with c3:
    st.metric("连续打卡", f"{streak} 天")

st.markdown("---")
st.subheader("🔔 浏览器提醒（实验）")

remind_time = st.time_input("每天提醒时间", value=dt_time(21, 0))
remind_hhmm = remind_time.strftime("%H:%M")

st.components.v1.html(
    f"""
    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
      <button id="hm_req">启用通知权限</button>
      <button id="hm_test">测试通知</button>
      <span style="opacity:.8">当前设定：每天 {remind_hhmm}（需要浏览器打开此站点页面）</span>
    </div>
    <script>
      const KEY = "healmate_remind_time";
      localStorage.setItem(KEY, "{remind_hhmm}");
      const req = document.getElementById("hm_req");
      const test = document.getElementById("hm_test");
      req.onclick = async () => {{
        if (!("Notification" in window)) return;
        await Notification.requestPermission();
      }};
      test.onclick = () => {{
        if (!("Notification" in window)) return;
        if (Notification.permission !== "granted") return;
        new Notification("HealMate 提醒", {{ body: "我在这里～今天感觉怎么样？来打个卡吧。" }});
      }};

      function scheduleOnce() {{
        if (window.__healmateScheduled) return;
        window.__healmateScheduled = true;
        if (!("Notification" in window)) return;
        if (Notification.permission !== "granted") return;
        const t = localStorage.getItem(KEY) || "{remind_hhmm}";
        const [hh, mm] = t.split(":").map(x => parseInt(x, 10));
        const now = new Date();
        const next = new Date();
        next.setHours(hh, mm, 0, 0);
        if (next <= now) next.setDate(next.getDate() + 1);
        const delay = next.getTime() - now.getTime();
        setTimeout(() => {{
          new Notification("HealMate 每日提醒", {{ body: "来完成今天的打卡吧～" }});
          window.__healmateScheduled = false;
          scheduleOnce();
        }}, delay);
      }}
      scheduleOnce();
    </script>
    """,
    height=70,
)

st.markdown("---")
st.subheader("📒 打卡记录")

if not records:
    st.write("暂无过往打卡记录。")
else:
    for record in records:
        date_str = record["date"]
        tasks_done = record["tasks"]
        user_feedback = record["feedback"]
        ai_msg = record["ai_reply"]
        try:
            dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
            display_date = dt_obj.strftime("%Y年%m月%d日")
        except ValueError:
            display_date = date_str

        with st.expander(f"📌 {display_date} - 完成 {len(tasks_done)} 项", expanded=False):
            if tasks_done:
                for t in tasks_done:
                    st.markdown(f"- ✅ {t}")
            else:
                st.markdown("那天在休息，没有完成任务，也没关系~")
            if user_feedback:
                st.markdown(f"> 📝 **你的感受：** {user_feedback}")
            if ai_msg:
                st.markdown(f"**💌 AI 的回应：**\n{ai_msg}")
