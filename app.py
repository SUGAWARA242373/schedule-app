import streamlit as st
import pandas as pd
import calendar
import datetime
import json
import os
import jpholiday

# =========================
# ページ設定
# =========================
st.set_page_config(layout="wide")
# =========================
# 年月入力（ここが唯一）
# =========================
year = st.number_input("年", value=2026, key="year_input")
month = st.number_input("月", 1, 12, 6, key="month_input")

days = calendar.monthrange(year, month)[1]
today = datetime.date.today()
data_file = f"data_{year}_{month}.json"
# =========================
# タイトル・年月（大表示）
# =========================
st.markdown(
    f"""
    <div style="font-size:48px;font-weight:800;margin-bottom:4px;">
        品質管理チーム月間スケジュール表
    </div>
    <div style="font-size:40px;font-weight:700;margin-bottom:24px;">
        {year}年 {month}月
    </div>
    """,
    unsafe_allow_html=True
)



# =========================
# CSS（1回だけ・コメント無し）
# =========================
st.markdown("""
<style>
div[data-testid="stVerticalBlock"] {
    gap: 0.02rem !important;
}

div[data-testid="stTextInput"] input {
    height: 50px !important;
    padding: 2px 6px !important;
    line-height: 1.1 !important;
    font-size: 22px !important;
    text-align: center !important;
    box-sizing: border-box !important;
}

textarea {
    min-height: 50px !important;
    padding: 2px 6px !important;
    line-height: 1.1 !important;
    font-size: 16px !important;
    box-sizing: border-box !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 初期化
# =========================
if "schedule" not in st.session_state:
    st.session_state.schedule = {}
if "duty" not in st.session_state:
    st.session_state.duty = {}

for d in range(1, days + 1):
    st.session_state.schedule.setdefault(d, "")
    st.session_state.duty.setdefault(d, "")
    st.session_state.setdefault(f"sch_{d}", "")
    st.session_state.setdefault(f"duty_{d}", "")

# =========================
# データロード（初回のみ）
# =========================
if os.path.exists(data_file) and not st.session_state.get("loaded", False):
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
    st.session_state.loaded = True

# =========================
# サイドバー：操作
# =========================
st.sidebar.header("操作")

templates = ["", "うわかい", "外船", "チーム会議", "安全衛生委員会", "在庫調査日"]
temp = st.sidebar.selectbox("予定テンプレ", templates)
day_sel = st.sidebar.number_input("日付", 1, days, 1)

if st.sidebar.button("テンプレ入力") and temp:
    cur = st.session_state.schedule[day_sel]
    val = temp if cur == "" else f"{cur} / {temp}"
    st.session_state.schedule[day_sel] = val
    st.session_state[f"sch_{day_sel}"] = val
    st.rerun()

members = ["菅原","阿部","澤","畠山","猿田","谷川","村手","武藤","小笠原","藤田"]
start = st.sidebar.selectbox("開始当番（1日）", members)

if st.sidebar.button("当番自動割当（平日のみ）"):
    idx = members.index(start)
    for d in range(1, days + 1):
        date = datetime.date(year, month, d)
        if date.weekday() >= 5 or jpholiday.is_holiday(date):
            st.session_state.duty[d] = ""
            st.session_state[f"duty_{d}"] = ""
            continue
        val = members[idx % len(members)]
        st.session_state.duty[d] = val
        st.session_state[f"duty_{d}"] = val
        idx += 1
    st.rerun()

if st.sidebar.button("全クリア"):
    for d in range(1, days + 1):
        st.session_state.schedule[d] = ""
        st.session_state.duty[d] = ""
        st.session_state[f"sch_{d}"] = ""
        st.session_state[f"duty_{d}"] = ""
    st.rerun()

# =========================
# 曜日色
# =========================
def get_color(d):
    wd = datetime.date(year, month, d).weekday()
    if wd == 5:
        return "blue"
    if wd == 6:
        return "red"
    return "black"

# =========================
# 表示
# =========================

def draw(d):
    c1, c2, c3 = st.columns([1, 1.5, 6])

    with c1:
        color = get_color(d)
        mark = "★" if datetime.date(year, month, d) == today else ""
        st.markdown(
            f"<div style='color:{color};font-size:22px'>{d}{mark}</div>",
            unsafe_allow_html=True
        )

    with c2:
        st.text_input("", key=f"duty_{d}", placeholder="当番")

    with c3:
        st.text_area("", key=f"sch_{d}", placeholder="予定", height=60)

   

colL, colR = st.columns(2)
with colL:
    for d in range(1, min(16, days + 1)):
        draw(d)
with colR:
    for d in range(16, days + 1):
        draw(d)

# =========================
# CSV保存
# =========================
if st.button("CSV保存"):
    df = pd.DataFrame({
        "日": list(range(1, days + 1)),
        "当番": [st.session_state.duty[d] for d in range(1, days + 1)],
        "予定": [st.session_state.schedule[d] for d in range(1, days + 1)]
    })
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("CSVダウンロード", csv, f"schedule_{year}_{month}.csv", "text/csv")

uploaded = st.file_uploader("CSV読込", type="csv")

if uploaded:
    df_in = pd.read_csv(uploaded)

    for _, row in df_in.iterrows():
        d = int(row["日"])
        if 1 <= d <= days:
            duty_val = "" if pd.isna(row["当番"]) else str(row["当番"])
            sch_val = "" if pd.isna(row["予定"]) else str(row["予定"])

            st.session_state.duty[d] = duty_val
            st.session_state.schedule[d] = sch_val

            st.session_state[f"duty_{d}"] = duty_val
            st.session_state[f"sch_{d}"] = sch_val

    st.success("CSVを読み込みました")
    st.rerun()

# =========================
# 自動保存
# =========================
with open(data_file, "w", encoding="utf-8") as f:
    json.dump(
        {"schedule": st.session_state.schedule, "duty": st.session_state.duty},
        f,
        ensure_ascii=False,
        indent=2
    )
