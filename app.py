import streamlit as st
import pandas as pd
import calendar
import datetime
import json
import os
import jpholiday

# =========================
# 基本設定
# =========================
st.set_page_config(layout="wide")

st.markdown("""
<style>
input::placeholder { font-size:11px; color:#999; }
input { font-size:13px; }
</style>
""", unsafe_allow_html=True)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# =========================
# 年月選択
# =========================
col_y, col_m = st.columns([2, 1])
with col_y:
    year = st.number_input("年", value=2026, step=1, key="year")
with col_m:
    month = st.number_input("月", 1, 12, 6, key="month")

days = calendar.monthrange(year, month)[1]
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
    "duty": {},
    "month": {"start": "", "container": [], "sample": [], "oil": []}
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
# 月次当番（表示）
# =========================
ms = st.session_state.data["month"]

st.markdown("### 月次当番")
st.markdown(
    f"""
    <div style="border:1px solid #ddd;padding:8px">
    開始当番：<b>{ms["start"]}</b><br>
    容器：{", ".join(ms["container"])}<br>
    サンプル：{", ".join(ms["sample"])}<br>
    灯油：{", ".join(ms["oil"])}
    </div>
    """,
    unsafe_allow_html=True
)

# =========================
# コールバック関数群（★核心）
# =========================
members = ["菅原","阿部","澤","畠山","猿田","谷川","村手","武藤","小笠原","藤田"]

def apply_template():
    d = str(st.session_state.day_sel)
    temp = st.session_state.temp_sel
    if temp == "":
        return
    cur = st.session_state.data["schedule"][d]
    st.session_state.data["schedule"][d] = temp if cur == "" else f"{cur} / {temp}"
    st.session_state.pop(f"sch_{d}", None)

def auto_assign():
    start = st.session_state.start_member
    idx = members.index(start)
    for d in range(1, days + 1):
        date = datetime.date(year, month, d)
        if date.weekday() >= 5 or jpholiday.is_holiday(date):
            continue
        st.session_state.data["duty"][str(d)] = members[idx % len(members)]
        st.session_state.pop(f"duty_{d}", None)
        idx += 1

def clear_all():
    for d in range(1, days + 1):
        st.session_state.data["schedule"][str(d)] = ""
        st.session_state.data["duty"][str(d)] = ""
        st.session_state.pop(f"sch_{d}", None)
        st.session_state.pop(f"duty_{d}", None)

# =========================
# サイドバー
# =========================
st.sidebar.header("操作・月次設定")

st.sidebar.selectbox(
    "予定テンプレ",
    ["", "チーム会議", "外船", "安全衛生委員会","うわかい","会議","監査"],
    key="temp_sel"
)

st.sidebar.number_input(
    "日付",
    1, days, 1,
    key="day_sel"
)

st.sidebar.button(
    "テンプレ入力",
    on_click=apply_template
)

st.sidebar.selectbox(
    "開始当番（1日）",
    members,
    key="start_member"
)

st.sidebar.button(
    "当番自動割当（土日祝除外）",
    on_click=auto_assign
)

st.sidebar.markdown("---")

ms["start"] = st.sidebar.selectbox("開始当番メンバー", members, index=members.index(ms["start"]) if ms["start"] in members else 0)
ms["container"] = st.sidebar.multiselect("容器", members, max_selections=3, default=ms["container"])
ms["sample"] = st.sidebar.multiselect("サンプル", members, max_selections=3, default=ms["sample"])
ms["oil"] = st.sidebar.multiselect("灯油", members, max_selections=3, default=ms["oil"])

st.sidebar.markdown("---")
st.sidebar.button("全削除（この月）", on_click=clear_all)

# =========================
# 表（入力部）
# =========================
def draw_day(d):
    k = str(d)
    c1, c2, c3 = st.columns([0.6, 1.8, 7])
    with c1:
        st.write(d)
    with c2:
        st.session_state.data["duty"][k] = st.text_input(
            "",
            st.session_state.data["duty"][k],
            key=f"duty_{d}",
            label_visibility="collapsed"
        )
    with c3:
        st.session_state.data["schedule"][k] = st.text_input(
            "",
            st.session_state.data["schedule"][k],
            key=f"sch_{d}",
            label_visibility="collapsed"
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
