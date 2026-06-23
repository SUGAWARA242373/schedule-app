
import streamlit as st
import pandas as pd
import calendar
import datetime
import json
import os
import jpholiday

def prev_month_info(year, month):
    if month == 1:
        return year - 1, 12
    return year, month - 1

def next_month_info(year, month):
    if month == 12:
        return year + 1, 1
    return year, month + 1

today = datetime.date.today()

year = today.year
month = today.month

prev_y, prev_m = prev_month_info(year, month)
next_y, next_m = next_month_info(year, month)


st.set_page_config(layout="wide")

# =========================
# 年月入力（唯一）
# =========================
year = st.number_input("年", value=2026, key="year_input")
month = st.number_input("月", 1, 12, 6, key="month_input")

days = calendar.monthrange(year, month)[1]
today = datetime.date.today()
data_file = f"data_{year}_{month}.json"
next_y, next_m = next_month_info(year, month)
next_days = calendar.monthrange(next_y, next_m)[1]
# =========================
# タイトル
# =========================
st.markdown(
    f"""
    <div style="font-size:40px;font-weight:800;">
        品質管理チーム月間スケジュール表
    </div>
    <div style="font-size:32px;margin-bottom:20px;">
        {year}年 {month}月
    </div>
    """,
    unsafe_allow_html=True
)

# =========================
# CSS
# =========================
st.markdown("""
<style>
div[data-testid="stVerticalBlock"] { gap: 0.02rem !important; }
div[data-testid="stTextInput"] input {
    height: 48px !important;
    font-size: 22px !important;
    text-align: center !important;
}
textarea { min-height: 50px !important; font-size: 16px !important; }
</style>
""", unsafe_allow_html=True)

# =========================
# widget state 初期化
# =========================
for d in range(1, days + 1):
    st.session_state.setdefault(f"duty_{d}", "")
    st.session_state.setdefault(f"sch_{d}", "")

# =========================
# 翌月分 widget state 初期化（⑤）
# =========================
for d in range(1, next_days + 1):
    st.session_state.setdefault(
        f"duty_{next_y}_{next_m}_{d}",
        ""
    )
    st.session_state.setdefault(
        f"sch_{next_y}_{next_m}_{d}",
        ""
    )

# =========================
# JSONロード（初回のみ）
# =========================
if os.path.exists(data_file) and not st.session_state.get("loaded", False):
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        for k, v in data.items():
            st.session_state[k] = v
    st.session_state.loaded = True

# =========================
# サイドバー：操作
# =========================
st.sidebar.header("操作")

day_sel = st.sidebar.number_input(
    "日付",
    1,
    days,
    1,
    key="day_select"
)

templates = ["", "うわかい", "外船", "チーム会議", "安全衛生委員会", "在庫調査日"]
temp = st.sidebar.selectbox(
    "予定テンプレ",
    templates,
    key="template_select"
)

if st.sidebar.button("テンプレ入力") and temp:
    cur = st.session_state[f"sch_{day_sel}"]
    st.session_state[f"sch_{day_sel}"] = temp if cur == "" else f"{cur} / {temp}"

members = ["菅原","阿部","澤","畠山","猿田","谷川","村手","武藤","小笠原","藤田"]
start = st.sidebar.selectbox(
    "開始当番（1日）",
    members,
    key="start_member"
)

if st.sidebar.button("当番自動割当（平日のみ）"):
    idx = members.index(start)
    for d in range(1, days + 1):
        date = datetime.date(year, month, d)
        if date.weekday() >= 5 or jpholiday.is_holiday(date):
            st.session_state[f"duty_{d}"] = ""
        else:
            st.session_state[f"duty_{d}"] = members[idx % len(members)]
            idx += 1

if st.sidebar.button("全クリア"):
    for d in range(1, days + 1):
        st.session_state[f"duty_{d}"] = ""
        st.session_state[f"sch_{d}"] = ""

# =========================
# 表示
# =========================

def next_month_info(year, month):
    if month == 12:
        return year + 1, 1
    return year, month + 1


def get_color_month(d, y, m):
    wd = datetime.date(y, m, d).weekday()

    if wd == 5:
        return "blue"

    if wd == 6:
        return "red"

    return "black"



# =========================
# CSV読込（最終・安全版）
# =========================
uploaded = st.file_uploader("CSV読込", type="csv")

if uploaded is not None and "csv_pending" not in st.session_state:
    st.session_state["csv_buffer"] = pd.read_csv(uploaded)
    st.session_state["csv_pending"] = True
    st.rerun()

if st.session_state.get("csv_pending", False):
    df_in = st.session_state.pop("csv_buffer")
    st.session_state.pop("csv_pending", None)

    for _, row in df_in.iterrows():
        d = int(row["日"])
        if 1 <= d <= days:   # ← ★ここが重要
            st.session_state[f"duty_{d}"] = (
                "" if pd.isna(row["当番"]) else str(row["当番"])
            )
            st.session_state[f"sch_{d}"] = (
                "" if pd.isna(row["予定"]) else str(row["予定"])
            )

    st.success("CSVを読み込みました")


def draw(d, y, m):
    c1, c2, c3 = st.columns([1, 2, 6])

    with c1:
        mark = "★" if datetime.date(y, m, d) == today else ""

        st.markdown(
            f"<div style='color:{get_color_month(d,y,m)};font-size:22px'>{d}{mark}</div>",
            unsafe_allow_html=True
        )

    with c2:
        st.text_input("", key=f"duty_{d}", placeholder="当番")

    with c3:
        st.text_area("", key=f"sch_{d}", placeholder="予定", height=50)


month1, month2 = st.columns(2)

with month1:

    st.subheader(f"{year}年 {month}月")

    left,right = st.columns(2)

    with left:
        for d in range(1, min(16, days + 1)):
            draw(d, year, month)

    with right:
        for d in range(16, days + 1):
            draw(d, year, month)

with month2:

    st.subheader(f"{next_y}年 {next_m}月")

    left,right = st.columns(2)

    with left:
        for d in range(1, min(16, next_days + 1)):
            draw(d, next_y, next_m)

    with right:
        for d in range(16, next_days + 1):
            draw(d, next_y, next_m)


# =========================
# CSV保存
# =========================
if st.button("CSV保存"):
    df = pd.DataFrame({
        "日": list(range(1, days + 1)),
        "当番": [st.session_state[f"duty_{d}"] for d in range(1, days + 1)],
        "予定": [st.session_state[f"sch_{d}"] for d in range(1, days + 1)],
    })
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "CSVダウンロード",
        csv,
        f"schedule_{year}_{month}.csv",
        "text/csv"
    )


# =========================
# 自動保存
# =========================
save_data = {
    k: v for k, v in st.session_state.items()
    if k.startswith("duty_") or k.startswith("sch_")
}
with open(data_file, "w", encoding="utf-8") as f:
    json.dump(save_data, f, ensure_ascii=False, indent=2)
