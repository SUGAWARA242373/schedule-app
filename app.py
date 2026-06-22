import streamlit as st
import pandas as pd
import calendar
import datetime
import json
import os
import jpholiday

# =================================================
# 基本設定
# =================================================
st.set_page_config(layout="wide")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# =================================================
# 年月選択
# =================================================
c1, c2 = st.columns([2,1])
with c1:
    year = st.number_input("年", value=2026, step=1)
with c2:
    month = st.number_input("月", min_value=1, max_value=12, value=6)

days = calendar.monthrange(year, month)[1]
today = datetime.date.today()
data_file = f"{DATA_DIR}/data_{year}_{month}.json"

# =================================================
# 月変更検知
# =================================================
if (
    "current_year" not in st.session_state
    or st.session_state.current_year != year
    or st.session_state.current_month != month
):
    st.session_state.clear()
    st.session_state.current_year = year
    st.session_state.current_month = month
    st.session_state.loaded = False

# =================================================
# データ（唯一の真実）
# =================================================
st.session_state.setdefault("data", {
    "schedule": {},
    "duty": {},
    "month_settings": {}
})

# =================================================
# データロード
# =================================================
if os.path.exists(data_file) and not st.session_state.loaded:
    with open(data_file, "r", encoding="utf-8") as f:
        st.session_state.data = json.load(f)
    st.session_state.loaded = True

# ✅ 日付キー補完（strで統一）
for d in range(1, days + 1):
    st.session_state.data["schedule"].setdefault(str(d), "")
    st.session_state.data["duty"].setdefault(str(d), "")

# =================================================
# タイトル（月名を強調）
# =================================================
st.markdown(
    f"<h1 style='font-size:44px'>品質管理チーム 月間スケジュール</h1>"
    f"<h2 style='font-size:32px;color:#444'>{year}年 {month}月</h2>",
    unsafe_allow_html=True
)

# =================================================
# 月次当番（表の上に表示）
# =================================================
members = ["菅原","阿部","澤","畠山","猿田","谷川","村手","武藤","小笠原","藤田"]

ms = st.session_state.data["month_settings"]

st.markdown("### 月次当番")
st.markdown(
    f"""
    <div style='padding:8px;border:1px solid #ddd;border-radius:6px'>
    開始当番：<b>{ms.get("start","")}</b><br>
    容器：{", ".join(ms.get("container", []))}<br>
    サンプル：{", ".join(ms.get("sample", []))}<br>
    灯油：{", ".join(ms.get("oil", []))}
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# =================================================
# サイドバー：操作・月次設定
# =================================================
st.sidebar.header("操作・月次設定")

templates = {
    "うわかい": "うわかい",
    "外船": "外船",
    "チーム会議": "チーム会議",
    "安全衛生委員会": "安全衛生委員会",
    "在庫調査日": "在庫調査日",
}

temp = st.sidebar.selectbox("予定テンプレ", [""] + list(templates.keys()))
day_sel = st.sidebar.number_input("日付", 1, days, 1)

if st.sidebar.button("テンプレ入力"):
    d = str(day_sel)
    cur = st.session_state.data["schedule"].get(d, "")
    st.session_state.data["schedule"][d] = (
        templates[temp] if cur == "" else f"{cur} / {templates[temp]}"
    )
    st.rerun()

st.sidebar.markdown("---")

start_member = st.sidebar.selectbox("開始当番（1日）", members)

if st.sidebar.button("当番自動割当（土日祝除外）"):
    idx = members.index(start_member)
    for d in range(1, days + 1):
        date = datetime.date(year, month, d)
        if date.weekday() >= 5 or jpholiday.is_holiday(date):
            continue
        st.session_state.data["duty"][str(d)] = members[idx % len(members)]
        idx += 1
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 月次設定")

st.session_state.data["month_settings"]["start"] = st.sidebar.selectbox(
    "開始当番メンバー",
    members,
    index=members.index(ms.get("start", members[0])),
    key="month_start"
)

def multi(title, key):
    st.session_state.data["month_settings"][key] = st.sidebar.multiselect(
        title,
        members,
        max_selections=3,
        default=ms.get(key, []),
        key=f"month_{key}"
    )

multi("容器", "container")
multi("サンプル", "sample")
multi("灯油", "oil")

# =================================================
# 表示（祝日背景・詰め）
# =================================================
def day_style(d):
    date = datetime.date(year, month, d)
    if jpholiday.is_holiday(date):
        return "#ffe5e5", "red"
    if date.weekday() == 5:
        return "#e8f0ff", "blue"
    if date.weekday() == 6:
        return "#ffe5e5", "red"
    return "white", "black"

def draw_day(d):
    key = str(d)
    bg, color = day_style(d)
    c1, c2, c3 = st.columns([1,2,7])

    with c1:
        st.markdown(
            f"<div style='background:{bg};color:{color};"
            f"font-size:24px;padding:2px'>{d}</div>",
            unsafe_allow_html=True
        )

    with c2:
        val = st.text_input("", value=st.session_state.data["duty"].get(key,""), key=f"duty_{d}", label_visibility="collapsed")
        st.session_state.data["duty"][key] = val

    with c3:
        val = st.text_input("", value=st.session_state.data["schedule"].get(key,""), key=f"sch_{d}", label_visibility="collapsed")
        st.session_state.data["schedule"][key] = val

colL, colR = st.columns(2)
with colL:
    for d in range(1, min(16, days + 1)):
        draw_day(d)
with colR:
    for d in range(16, days + 1):
        draw_day(d)

# =================================================
# 自動保存
# =================================================
with open(data_file, "w", encoding="utf-8") as f:
    json.dump(st.session_state.data, f, ensure_ascii=False, indent=2)
