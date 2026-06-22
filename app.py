import streamlit as st
import pandas as pd
import calendar
import datetime
import json
import os



  



# ✅ CSS（入力欄用）

st.set_page_config(layout="wide")

# 年月入力（★key付き）
year = st.number_input("年", value=2026, key="year_input")
month = st.number_input("月", 1, 12, 6, key="month_input")

# タイトル・年月表示（大）
st.markdown(
    f"""
    <div style="font-size:42px;font-weight:700;">
        品質管理チーム月間スケジュール表
    </div>
    <div style="font-size:34px;font-weight:600;margin-bottom:20px;">
        {year}年 {month}月
    </div>
    """,
    unsafe_allow_html=True
)


/* 行と行の間（全体） */
div[data-testid="stVerticalBlock"] {
    gap: 0.02rem !important;
}

/* 当番（text_input） */
div[data-testid="stTextInput"] input {
    height: 50px !important;
    padding-top: 1px !important;
    padding-bottom: 2px !important;
    padding-left: 6px !important;
    padding-right: 6px !important;
    line-height: 1.1 !important;
    font-size: 22px !important;
    text-align: center !important;
    box-sizing: border-box !important;
}

/* 予定（text_area） */
textarea {
    min-height: 50px !important;
    padding-top: 2px !important;
    padding-bottom: 2px !important;
    padding-left: 6px !important;
    padding-right: 6px !important;
    line-height: 1.1 !important;
    font-size: 16px !important;
    box-sizing: border-box !important;
}

</style>
""", unsafe_allow_html=True)

# =========================
# 月設定
# =========================
year = st.number_input("年", value=2026)
month = st.number_input("月", 1, 12, 6)

days = calendar.monthrange(year, month)[1]
today = datetime.date.today()

data_file = f"data_{year}_{month}.json"

# =========================
# 初期化（安全版）
# =========================
if "schedule" not in st.session_state:
    st.session_state.schedule = {}

if "duty" not in st.session_state:
    st.session_state.duty = {}

# 日数分補完（KeyError防止）
for d in range(1, days+1):
    st.session_state.schedule.setdefault(d, "")
    st.session_state.duty.setdefault(d, "")

# =========================
# UIキー初期化（超重要）
# =========================
for d in range(1, days+1):
    st.session_state.setdefault(f"duty_{d}", st.session_state.duty.get(d, ""))
    st.session_state.setdefault(f"sch_{d}", st.session_state.schedule.get(d, ""))

# =========================
# 初回ロード
# =========================
if os.path.exists(data_file) and "loaded" not in st.session_state:
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
# サイドバー：テンプレ
# =========================
st.sidebar.header("操作")

templates = {
    "うわかい": "うわかい",
    "外船": "外船",
    "チーム会議": "チーム会議",
    "安全衛生委員会": "安全衛生委員会",
    "在庫調査日": "在庫調査日"
}

temp = st.sidebar.selectbox("予定テンプレ", [""] + list(templates.keys()))
day_sel = st.sidebar.number_input("日付", 1, days, 1)

if st.sidebar.button("テンプレ入力"):
    if temp:
        if st.session_state.schedule[day_sel] == "":
            val = templates[temp]
        else:
            val = st.session_state.schedule[day_sel] + " / " + templates[temp]

        st.session_state.schedule[day_sel] = val
        st.session_state[f"sch_{day_sel}"] = val

    st.rerun()

# =========================
# 当番自動ローテ
# =========================
members = ["菅原","阿部","澤","畠山","猿田","谷川","村手","武藤","小笠原","藤田"]

start = st.sidebar.selectbox("開始当番（1日）", members)

import jpholiday  # ← 忘れずに

if st.sidebar.button("当番自動割当"):
    idx = members.index(start)

    for d in range(1, days+1):
        date = datetime.date(year, month, d)

        # 土日 or 祝日はスキップ
        if date.weekday() >= 5 or jpholiday.is_holiday(date):
            st.session_state.duty[d] = ""
            st.session_state[f"duty_{d}"] = ""
            continue

        val = members[idx % len(members)]
        st.session_state.duty[d] = val
        st.session_state[f"duty_{d}"] = val
        idx += 1

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
        today_mark = "★" if datetime.date(year, month, d) == today else ""
        st.markdown(
            f"<div style='color:{color}; font-size:22px'>{d}{today_mark}</div>",
            unsafe_allow_html=True
        )

    with c2:
        st.text_input(
            "",
            key=f"duty_{d}",
            placeholder="当番"
        )

    with c3:
        st.text_area(
            "",
            key=f"sch_{d}",
            placeholder="予定",
            height=60
        )

    # UIキー → データ同期（これだけ）
    st.session_state.duty[d] = st.session_state.get(f"duty_{d}", "")
    st.session_state.schedule[d] = st.session_state.get(f"sch_{d}", "")


# 表（左右2列）
colL, colR = st.columns(2)

with colL:
    for d in range(1, min(16, days+1)):
        draw(d)

with colR:
    for d in range(16, days+1):
        draw(d)

# =========================
# CSV保存
# =========================
# =========================
# CSV保存
# =========================
if st.button("CSV保存"):
    df = pd.DataFrame({
        "日": list(range(1, days+1)),
        "当番": [st.session_state.duty[d] for d in range(1, days+1)],
        "予定": [st.session_state.schedule[d] for d in range(1, days+1)]
    })

    # ローカル保存（今まで通り）
    df.to_csv(f"schedule_{year}_{month}.csv", index=False)

    # ✅ 追加：ダウンロード用CSV生成
    csv = df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="CSVダウンロード",
        data=csv,
        file_name=f"schedule_{year}_{month}.csv",
        mime="text/csv"
    )

    st.success("保存完了（ダウンロード可）")



# =========================
# 全クリア（重要修正済）
# =========================
if st.button("全クリア"):
    for d in range(1, days+1):

        st.session_state.schedule[d] = ""
        st.session_state.duty[d] = ""

        if f"duty_{d}" in st.session_state:
            del st.session_state[f"duty_{d}"]

        if f"sch_{d}" in st.session_state:
            del st.session_state[f"sch_{d}"]

    st.rerun()

# =========================
# 自動保存
# =========================
data = {
    "schedule": st.session_state.schedule,
    "duty": st.session_state.duty
}

with open(data_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
