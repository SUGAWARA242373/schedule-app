import streamlit as st
import calendar
import datetime
import json
import os
import jpholiday

# =========================
# ページ設定
# =========================
st.set_page_config(layout="wide")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# =========================
# 年月選択
# =========================
c1, c2 = st.columns([2, 1])
with c1:
    year = st.number_input("年", value=2026, step=1)
with c2:
    month = st.number_input("月", 1, 12, 6)

days = calendar.monthrange(year, month)[1]
today = datetime.date.today()
data_file = f"{DATA_DIR}/data_{year}_{month}.json"

# =========================
# 月変更検知
# =========================
if (
    "cur_year" not in st.session_state
    or st.session_state.cur_year != year
    or st.session_state.cur_month != month
):
    st.session_state.clear()
    st.session_state.cur_year = year
    st.session_state.cur_month = month
    st.session_state.loaded = False

# =========================
# データ（唯一の正）
# =========================
st.session_state.setdefault("data", {
    "schedule": {},
    "duty": {}
})

# =========================
# データロード
# =========================
if os.path.exists(data_file) and not st.session_state.loaded:
    with open(data_file, "r", encoding="utf-8") as f:
        st.session_state.data = json.load(f)
    st.session_state.loaded = True

# 補完
for d in range(1, days + 1):
    st.session_state.data["schedule"].setdefault(str(d), "")
    st.session_state.data["duty"].setdefault(str(d), "")

# =========================
# タイトル
# =========================
st.markdown(
    f"<h1>品質管理チーム 月間スケジュール</h1>"
    f"<h2>{year}年 {month}月</h2>",
    unsafe_allow_html=True
)

# =========================
# コールバック関数（★必須）
# =========================
def update_schedule(day):
    st.session_state.data["schedule"][day] = st.session_state[f"sch_{day}"]

def update_duty(day):
    st.session_state.data["duty"][day] = st.session_state[f"duty_{day}"]

def apply_template():
    d = str(st.session_state.day_sel)
    temp = st.session_state.temp_sel
    if temp == "":
        return
    st.session_state.data["schedule"][d] = temp
    st.session_state.pop(f"sch_{d}", None)

def clear_all():
    for d in range(1, days + 1):
        st.session_state.data["schedule"][str(d)] = ""
        st.session_state.data["duty"][str(d)] = ""
        st.session_state.pop(f"sch_{d}", None)
        st.session_state.pop(f"duty_{d}", None)

# =========================
# サイドバー
# =========================
st.sidebar.header("操作")

st.sidebar.selectbox(
    "予定テンプレ",
    ["", "チーム会議", "外船", "安全衛生委員会"],
    key="temp_sel"
)

st.sidebar.number_input(
    "日付",
    1, days, 1,
    key="day_sel"
)

st.sidebar.button("テンプレ入力", on_click=apply_template)
st.sidebar.button("全削除", on_click=clear_all)

# =========================
# 日付スタイル
# =========================
def day_style(d):
    date = datetime.date(year, month, d)
    if jpholiday.is_holiday(date):
        return "#ffe5e5", "red"
    if date.weekday() == 5:
        return "#e8f0ff", "blue"
    if date.weekday() == 6:
        return "#ffe5e5", "red"
    return "white", "black"

# =========================
# 表示
# =========================
def draw_day(d):
    key = str(d)
    bg, color = day_style(d)
    mark = "★" if datetime.date(year, month, d) == today else ""

    c1, c2, c3 = st.columns([0.6, 1.8, 7])

    with c1:
        st.markdown(
            f"<div style='background:{bg};color:{color};padding:2px'>{d}{mark}</div>",
            unsafe_allow_html=True
        )

    with c2:
        st.text_input(
            "",
            value=st.session_state.data["duty"][key],
            key=f"duty_{d}",
            label_visibility="collapsed",
            on_change=update_duty,
            args=(key,)
        )

    with c3:
        st.text_input(
            "",
            value=st.session_state.data["schedule"][key],
            key=f"sch_{d}",
            label_visibility="collapsed",
            on_change=update_schedule,
            args=(key,)
        )

left, right = st.columns(2)
with left:
    for d in range(1, min(16, days + 1)):
        draw_day(d)
with right:
    for d in range(16, days + 1):
        draw_day(d)

# =========================
# 自動保存
# =========================
with open(data_file, "w", encoding="utf-8") as f:
    json.dump(st.session_state.data, f, ensure_ascii=False, indent=2)
