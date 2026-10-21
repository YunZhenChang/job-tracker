"""求職進度追蹤器（Streamlit 版）

執行方式：
    pip install -r requirements.txt
    streamlit run app.py

預設為展示模式（PERSIST = False）：資料只留在目前這次瀏覽，適合公開部署。
若要在自己的電腦長期使用，請把下面的 PERSIST 改成 True，
資料會存在 app.py 旁邊的 jobs.json（務必不要上傳到 GitHub）。
"""
import json
import re
import uuid
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
import altair as alt

# ===== 設定 =====
STATUSES = ["已投遞", "面試中", "已獲 Offer", "未錄取", "已撤回"]
DATA_FILE = Path(__file__).with_name("jobs.json")
PERSIST = False  # False：展示模式，資料只留在這次瀏覽；True：存到 jobs.json（本機長期使用）


# ===== 資料讀寫 =====
def load_items():
    """讀取 jobs.json；檔案不存在或內容壞掉時回傳空清單。"""
    if not PERSIST or not DATA_FILE.exists():
        return []
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def save_items():
    """把目前的紀錄寫回 jobs.json；失敗時提醒使用者而不是讓程式當掉。"""
    if not PERSIST:
        return
    try:
        DATA_FILE.write_text(
            json.dumps(st.session_state.jobs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        st.warning("無法寫入 jobs.json，資料只會保留到關閉頁面為止。")


def md_escape(text):
    """跳脫 Markdown 符號，避免使用者輸入的文字被當成格式指令顯示。"""
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|>~])", r"\\\1", str(text))


def set_status(item_id):
    """下拉選單改狀態時的回呼函式（callback）。"""
    new_status = st.session_state[f"status_{item_id}"]
    for it in st.session_state.jobs:
        if it["id"] == item_id:
            it["status"] = new_status
    save_items()


def load_demo():
    """範例資料：公司皆為虛構，讓第一次打開的人可以直接看到效果。"""
    d = lambda n: (date.today() + timedelta(days=n)).isoformat()
    st.session_state.jobs = [
        {"id": "d1", "company": "範例科技 A", "position": "後端工程師", "status": "面試中","applied": d(-10), "interview": d(3), "url": "", "notes": "一面通過，準備二面的系統設計題。"},
        {"id": "d2", "company": "範例數據 B", "position": "資料工程師", "status": "已投遞","applied": d(-4), "interview": "", "url": "", "notes": ""},
        {"id": "d3", "company": "範例軟體 C", "position": "AI 工程師", "status": "已獲 Offer","applied": d(-25), "interview": d(-12), "url": "", "notes": "薪資與到職日待確認。"},
        {"id": "d4", "company": "範例網路 D", "position": "前端工程師", "status": "未錄取","applied": d(-30), "interview": "", "url": "", "notes": ""},
    ]
    save_items()


# ===== 初始化（Streamlit 每次互動都會重跑整支程式，所以狀態要放進 session_state）=====
st.set_page_config(page_title="求職進度追蹤器", page_icon="📋", layout="wide")
if "jobs" not in st.session_state:
    st.session_state.jobs = load_items()
    st.session_state.editing_id = None
    st.session_state.pending_delete = None
    st.session_state.form_n = 0  # 每次成功新增就加 1，用來讓表單欄位重置

items = st.session_state.jobs
editing = next((it for it in items if it["id"] == st.session_state.editing_id), None)
suffix = editing["id"] if editing else f"new{st.session_state.form_n}"  # 欄位 key 的後綴

# ===== 側邊欄：新增或編輯表單 =====
with st.sidebar:
    st.header("編輯投遞紀錄" if editing else "新增投遞紀錄")
    with st.form("job_form"):
        company = st.text_input("公司名稱 *", value=editing["company"] if editing else "",
                                max_chars=60, key=f"company_{suffix}")
        position = st.text_input("職稱 *", value=editing["position"] if editing else "",max_chars=60, key=f"position_{suffix}")
        status = st.selectbox("狀態", STATUSES, key=f"status_form_{suffix}",index=STATUSES.index(editing["status"]) if editing else 0)
        applied = st.date_input(
            "投遞日期", key=f"applied_{suffix}",
            value=date.fromisoformat(editing["applied"]) if editing and editing["applied"] else date.today())
        has_interview = st.checkbox("有面試日期", key=f"has_iv_{suffix}",
                                    value=bool(editing and editing["interview"]))
        interview = st.date_input(
            "面試日期（勾選上方才會儲存）", key=f"interview_{suffix}",
            value=date.fromisoformat(editing["interview"]) if editing and editing["interview"] else date.today())
        url = st.text_input("職缺連結（選填）", value=editing["url"] if editing else "",
                            placeholder="https://", key=f"url_{suffix}")
        notes = st.text_area("備註（選填）", value=editing["notes"] if editing else "",max_chars=500, key=f"notes_{suffix}")
        submitted = st.form_submit_button("儲存變更" if editing else "新增紀錄", type="primary")

    if submitted:
        company, position, url = company.strip(), position.strip(), url.strip()
        if not company or not position:
            st.error("請填寫公司名稱與職稱。")
        elif url and not url.lower().startswith(("http://", "https://")):
            st.error("職缺連結請以 http:// 或 https:// 開頭。")
        else:
            record = {
                "id": editing["id"] if editing else uuid.uuid4().hex[:8],
                "company": company, "position": position, "status": status,
                "applied": applied.isoformat(),
                "interview": interview.isoformat() if has_interview else "",
                "url": url, "notes": notes.strip(),
            }
            if editing:
                st.session_state.jobs = [record if it["id"] == record["id"] else it for it in items]
            else:
                items.append(record)
                st.session_state.form_n += 1
            st.session_state.editing_id = None
            save_items()
            st.rerun()

    if editing and st.button("取消編輯"):
        st.session_state.editing_id = None
        st.rerun()

# ===== 主畫面：標題與統計 =====
st.title("求職進度追蹤器")
st.caption("記錄每一筆投遞的狀態與面試日期。")
if not PERSIST:
    st.caption("展示版：資料只保留在這次瀏覽中，重新整理頁面後會清空。可按「載入範例資料」體驗。")

if not items:
    st.info("從左側表單新增第一筆投遞紀錄，或先載入範例資料看看效果。")
    if st.button("載入範例資料"):
        load_demo()
        st.rerun()
    st.stop()  # 沒有資料就不用往下畫了

counts = {s: sum(1 for it in items if it["status"] == s) for s in STATUSES}
for col, s in zip(st.columns(len(STATUSES)), STATUSES):
    col.metric(s, counts[s])
chart_df = pd.DataFrame({"狀態": STATUSES, "數量": [counts[s] for s in STATUSES]})
st.altair_chart(
    alt.Chart(chart_df).mark_bar().encode(
        x=alt.X("狀態", sort=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("數量", axis=alt.Axis(tickMinStep=1)),
    ).properties(height=180),
    use_container_width=True,
)

# 提醒：7 天內（含今天）有面試的筆數
today, limit = date.today().isoformat(), (date.today() + timedelta(days=7)).isoformat()
soon = sum(1 for it in items if it["interview"] and today <= it["interview"] <= limit)
if soon:
    st.warning(f"7 天內有 {soon} 場面試")

# ===== 篩選、搜尋、排序 =====
c1, c2, c3 = st.columns([2, 2, 1.5])
query = c1.text_input("搜尋公司或職稱", placeholder="輸入關鍵字").strip().lower()
picked = c2.multiselect("狀態", STATUSES, default=STATUSES)
order = c3.selectbox("排序", ["投遞日期：新到舊", "投遞日期：舊到新", "公司名稱"])

view = [it for it in items
        if it["status"] in picked and query in (it["company"] + " " + it["position"]).lower()]
if order == "公司名稱":
    view.sort(key=lambda it: it["company"])
else:
    view.sort(key=lambda it: it["applied"], reverse=(order == "投遞日期：新到舊"))

if not view:
    st.info("沒有符合條件的紀錄，請調整搜尋或篩選。")

# ===== 列表 =====
for it in view:
    with st.container(border=True):
        left, right = st.columns([3, 1.2])
        left.markdown(f"**{md_escape(it['company'])}**　{md_escape(it['position'])}")
        right.selectbox(
            "狀態", STATUSES, key=f"status_{it['id']}", label_visibility="collapsed",
            index=STATUSES.index(it["status"]) if it["status"] in STATUSES else 0,
            on_change=set_status, args=(it["id"],))
        st.caption(f"投遞 {it['applied'] or '未填'}" + (f"　面試 {it['interview']}" if it["interview"] else ""))
        if it["notes"]:
            st.text(it["notes"])  # st.text 以純文字顯示，不會解析格式

        b1, b2, b3, _ = st.columns([1, 1, 1.2, 5])
        if it["url"].lower().startswith(("http://", "https://")):
            b1.link_button("職缺連結", it["url"])
        if b2.button("編輯", key=f"edit_{it['id']}"):
            st.session_state.editing_id = it["id"]
            st.rerun()
        if b3.button("刪除", key=f"del_{it['id']}"):
            st.session_state.pending_delete = it["id"]
            st.rerun()
        if st.session_state.pending_delete == it["id"]:  # 刪除前再確認一次
            st.warning("確定要刪除這筆紀錄嗎？")
            y, n, _ = st.columns([1, 1, 6])
            if y.button("確定刪除", key=f"yes_{it['id']}"):
                st.session_state.jobs = [x for x in items if x["id"] != it["id"]]
                st.session_state.pending_delete = None
                if st.session_state.editing_id == it["id"]:
                    st.session_state.editing_id = None
                save_items()
                st.rerun()
            if n.button("取消", key=f"no_{it['id']}"):
                st.session_state.pending_delete = None
                st.rerun()

# ===== 清除全部 =====
with st.expander("清除全部資料"):
    if st.checkbox("我了解這會刪除所有紀錄，且無法復原") and st.button("清除全部"):
        st.session_state.jobs = []
        st.session_state.editing_id = st.session_state.pending_delete = None
        save_items()
        st.rerun()
