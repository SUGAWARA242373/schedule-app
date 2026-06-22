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

st.markdown(
    "<h1 style='font-size:38px'>品質管理チーム 月間スケジュール</h1>",
    unsafe_allow_html=True
)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# =================================================
# 年月選択（文字大）
# =================================================
c_y, c_m = st.columns([2,1])
with c_y:
    year = st.number_input("年", value=2026, step=1)
with c_m:
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

for d in range(1, days + 1):
    st.session_state.data["schedule"].setdefault(d, "")
    st.session_state.data["duty"].setdefault(d, "")

# =================================================
# データロード
# =================================================
if os.path.exists(data_file) and not st.session_state.loaded:
    with open(data_file, "r", encoding="utf-8") as f:
        st.session_state.data = json.load(f)
    st.session_state.loaded = True

# =================================================
# サイドバー（操作＋月次当番を1画面）
# =================================================
st.sidebar.header("操作・月次設定")

members = ["菅原","阿部","澤","畠山","猿田","谷川","村手","武藤","小笠原","藤田"]

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
    if temp:
        cur = st.session_state.data["schedule"][day_sel]
        st.session_state.data["schedule"][day_sel] = (
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
        st.session_state.data["duty"][d] = members[idx % len(members)]
        idx += 1
    st.rerun()

st.sidebar.markdown("---")

st.sidebar.markdown("### 月次当番")
st.session_state.data["month_settings"]["start"] = st.sidebar.selectbox(
    "開始当番メンバー",
    members,
    index=members.index(
        st.session_state.data["month_settings"].get("start", members[0])
    ),
    key="month_start"
)

def multi(title, key):
    st.sidebar.markdown(f"**{title}**")
    st.session_state.data["month_settings"][key] = st.sidebar.multiselect(
        "最大3名",
        members,
        max_selections=3,
        default=st.session_state.data["month_settings"].get(key, []),
        key=f"month_{key}"
    )

multi("容器", "container")
multi("サンプル", "sample")
multi("灯油", "oil")

# =================================================
# 表示部（祝日背景・行間詰め）
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
    bg, color = day_style(d)
    c1, c2, c3 = st.columns([1,2,7])

    with c1:
        st.markdown(
            f"<div style='background:{bg};color:{color};"
            f"font-size:26px;padding:4px'>{d}</div>",
            unsafe_allow_html=True
        )

    with c2:
        val = st.text_input(
            "",
            value=st.session_state.data["duty"][d],
            key=f"duty_{d}",
            label_visibility="collapsed"
        )
        st.session_state.data["duty"][d] = val

    with c3:
        val = st.text_input(
            "",
            value=st.session_state.data["schedule"][d],
            key=f"sch_{d}",
            label_visibility="collapsed"
        )
        st.session_state.data["schedule"][d] = val

colL, colR = st.columns(2)
with colL:
    for d in range(1, min(16, days + 1)):
        draw_day(d)
with colR:
    for d in range(16, days + 1):
        draw_day(d)

# =================================================
# CSV
# =================================================
st.sidebar.markdown("---")
uploaded = st.sidebar.file_uploader("CSV読込", type="csv")

if uploaded:
    df = pd.read_csv(uploaded)
    for _, r in df.iterrows():
        d = int(r["日"])
        st.session_state.data["duty"][d] = "" if pd.isna(r["当番"]) else str(r["当番"])
        st.session_state.data["schedule"][d] = "" if pd.isna(r["予定"]) else str(r["予定"])
    st.rerun()

if st.button("CSV保存"):
    df = pd.DataFrame({
        "日": range(1, days + 1),
        "当番": [st.session_state.data["duty"][d] for d in range(1, days + 1)],
        "予定": [st.session_state.data["schedule"][d] for d in range(1, days + 1)],
    })
    df.to_csv(f"schedule_{year}_{month}.csv", index=False)
    st.success("CSV保存完了")

# =================================================
# 自動保存
# =================================================
with open(data_file, "w", encoding="utf-8") as f:
    json.dump(st.session_state.data, f, ensure_ascii=False, indent=2)
