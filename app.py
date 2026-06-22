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
st.title("品質管理チーム 月間スケジュール（Web版）")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# =================================================
# 年月選択
# =================================================
year = st.number_input("年", value=2026, step=1)
month = st.number_input("月", min_value=1, max_value=12, value=6)

days = calendar.monthrange(year, month)[1]
today = datetime.date.today()

data_file = f"{DATA_DIR}/data_{year}_{month}.json"

# =================================================
# 月変更検知（Webツールの要）
# =================================================
if (
    "prev_year" not in st.session_state
    or st.session_state.prev_year != year
    or st.session_state.prev_month != month
):
    st.session_state.clear()
    st.session_state.prev_year = year
    st.session_state.prev_month = month
    st.session_state.loaded = False

# =================================================
# 初期化
# =================================================
st.session_state.setdefault("schedule", {})
st.session_state.setdefault("duty", {})
st.session_state.setdefault("month_settings", {})

for d in range(1, days + 1):
    st.session_state.schedule.setdefault(d, "")
    st.session_state.duty.setdefault(d, "")
    st.session_state.setdefault(f"sch_{d}", "")
    st.session_state.setdefault(f"duty_{d}", "")

# =================================================
# データロード
# =================================================
if os.path.exists(data_file) and not st.session_state.loaded:
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for k, v in data.get("schedule", {}).items():
        d = int(k)
        st.session_state.schedule[d] = v
        st.session_state[f"sch_{d}"] = v

    for k, v in data.get("duty", {}).items():
        d = int(k)
        st.session_state.duty[d] = v
        st.session_state[f"duty_{d}"] = v

    st.session_state.month_settings = data.get("month_settings", {})
    st.session_state.loaded = True

# =================================================
# サイドバー（操作パネル）
# =================================================
st.sidebar.header("操作")

# --- テンプレ入力 ---
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
        cur = st.session_state.schedule[day_sel]
        val = templates[temp] if cur == "" else f"{cur} / {templates[temp]}"
        st.session_state.schedule[day_sel] = val
        st.session_state[f"sch_{day_sel}"] = val
    st.rerun()

# --- 当番自動割当 ---
members = ["菅原","阿部","澤","畠山","猿田","谷川","村手","武藤","小笠原","藤田"]

start_member = st.sidebar.selectbox("開始当番（1日）", members)

if st.sidebar.button("当番自動割当"):
    idx = members.index(start_member)

    for d in range(1, days + 1):
        date = datetime.date(year, month, d)

        if date.weekday() >= 5 or jpholiday.is_holiday(date):
            st.session_state.duty[d] = ""
            st.session_state[f"duty_{d}"] = ""
            continue

        name = members[idx % len(members)]
        st.session_state.duty[d] = name
        st.session_state[f"duty_{d}"] = name
        idx += 1

    st.rerun()

# =================================================
# 月次設定（左下ブロック）
# =================================================
st.sidebar.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)

st.sidebar.markdown("### 月次当番")
with st.sidebar.container(border=True):
    st.session_state.month_settings["month_start"] = st.selectbox(
        "開始当番のメンバーを選択",
        members,
        index=members.index(
            st.session_state.month_settings.get("month_start", members[0])
        )
    )


def multi(title, key):
    st.sidebar.markdown(f"### {title}")
    with st.sidebar.container(border=True):
        st.session_state.month_settings[key] = st.multiselect(
            "開始当番のメンバーから最大3名を選択",
            members,
            max_selections=3,
            default=st.session_state.month_settings.get(key, []),
            key=f"month_{key}"   # ← 重複防止
        )


multi("容器", "container")
multi("サンプル", "sample")
multi("灯油", "oil")

# =================================================
# 表示部
# =================================================
def day_color(d):
    wd = datetime.date(year, month, d).weekday()
    if wd == 5:
        return "blue"
    if wd == 6:
        return "red"
    return "black"

def draw_day(d):
    c1, c2, c3 = st.columns([1, 2, 6])
    with c1:
        mark = "★" if datetime.date(year, month, d) == today else ""
        st.markdown(
            f"<div style='color:{day_color(d)}; font-size:28px'>{d}{mark}</div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.session_state.duty[d] = st.text_input("", key=f"duty_{d}")
    with c3:
        st.session_state.schedule[d] = st.text_input("", key=f"sch_{d}")

colL, colR = st.columns(2)
with colL:
    for d in range(1, min(16, days + 1)):
        draw_day(d)
with colR:
    for d in range(16, days + 1):
        draw_day(d)

# =================================================
# CSV入出力
# =================================================
st.sidebar.markdown("---")
uploaded = st.sidebar.file_uploader("CSV読込", type="csv")

if uploaded:
    df = pd.read_csv(uploaded)
    for _, r in df.iterrows():
        d = int(r["日"])
        st.session_state.duty[d] = str(r["当番"]) if not pd.isna(r["当番"]) else ""
        st.session_state.schedule[d] = str(r["予定"]) if not pd.isna(r["予定"]) else ""
        st.session_state[f"duty_{d}"] = st.session_state.duty[d]
        st.session_state[f"sch_{d}"] = st.session_state.schedule[d]
    st.rerun()

if st.button("CSV保存"):
    df = pd.DataFrame({
        "日": range(1, days + 1),
        "当番": [st.session_state.duty[d] for d in range(1, days + 1)],
        "予定": [st.session_state.schedule[d] for d in range(1, days + 1)],
    })
    df.to_csv(f"schedule_{year}_{month}.csv", index=False)
    st.success("CSV保存完了")

# =================================================
# 自動保存（Webツール必須）
# =================================================
with open(data_file, "w", encoding="utf-8") as f:
    json.dump(
        {
            "schedule": st.session_state.schedule,
            "duty": st.session_state.duty,
            "month_settings": st.session_state.month_settings,
        },
        f,
        ensure_ascii=False,
        indent=2,
    )
