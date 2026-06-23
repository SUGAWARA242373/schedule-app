import streamlit as st
import pandas as pd
import calendar
import datetime
import json
import os
import jpholiday

st.set_page_config(layout="wide")

# =========================
# 月計算
# =========================
def prev_month_info(year, month):
    if month == 1:
        return year - 1, 12
    return year, month - 1


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


today = datetime.date.today()



# =========================
# 年月入力
# =========================


st.sidebar.subheader("対象年月")

year = st.sidebar.selectbox(
    "年",
    list(range(2024, 2036)),
    index=today.year - 2024
)

month = st.sidebar.selectbox(
    "月",
    list(range(1, 13)),
    index=today.month - 1
)

days = calendar.monthrange(year, month)[1]

next_y, next_m = next_month_info(year, month)

next_days = calendar.monthrange(
    next_y,
    next_m
)[1]

data_file = f"data_{year}_{month}.json"


# =========================
# タイトル
# =========================

st.info(
    "入力内容は月毎に自動保存されます。"
)
st.markdown(
    f"""
    <div style="font-size:40px;font-weight:800;">
        品質管理チーム月間スケジュール表
    </div>
   
    """,
    unsafe_allow_html=True
)

# =========================
# CSS
# =========================
st.markdown("""
<style>

div[data-testid="stTextInput"] input{
    height:48px !important;
    font-size:14px !important;
}

div[data-testid="stTextArea"] textarea{
    min-height:48px !important;
    font-size:12px !important;
}

</style>
""", unsafe_allow_html=True)
# =========================
# State初期化（当月）
# =========================
for d in range(1, days + 1):

    st.session_state.setdefault(
        f"duty_{year}_{month}_{d}",
        ""
    )

    st.session_state.setdefault(
        f"sch_{year}_{month}_{d}",
        ""
    )

# =========================
# State初期化（翌月）
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

# 月間担当 初期化
# =========================
st.session_state.setdefault(
    f"safe_{year}_{month}",
    ""
)

st.session_state.setdefault(
    f"oil_{year}_{month}",
    []
)

st.session_state.setdefault(
    f"sample_{year}_{month}",
    []
)

st.session_state.setdefault(
    f"container_{year}_{month}",
    []
)


# =========================
# JSONロード
# =========================
if os.path.exists(data_file):

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for k, v in data.items():

        if k not in st.session_state:
            st.session_state[k] = v

        elif st.session_state[k] == "":
            st.session_state[k] = v

# =========================
# サイドバー
# =========================
st.sidebar.header("操作")

day_sel = st.sidebar.number_input(
    "日付",
    1,
    days,
    1
)

templates = [
    "",
    "うわかい",
    "外船",
    "チーム会議",
    "安全衛生委員会",
    "在庫調査日",
    
    ]

temp = st.sidebar.selectbox(
    "予定テンプレ",
    templates
)

if st.sidebar.button("テンプレ入力") and temp:

    key = f"sch_{year}_{month}_{day_sel}"

    cur = st.session_state[key]

    st.session_state[key] = (
        temp
        if cur == ""
        else f"{cur} / {temp}"
    )

members = [
    "菅原",
    "阿部",
    "澤",
    "畠山",
    "猿田",
    "谷川",
    "村手",
    "武藤",
    "小笠原",
    "藤田"
]

start = st.sidebar.selectbox(
    "開始当番（1日）",
    members
)

if st.sidebar.button("当番自動割当（平日のみ）"):

    idx = members.index(start)

    for d in range(1, days + 1):

        date = datetime.date(year, month, d)

        key = f"duty_{year}_{month}_{d}"

        if date.weekday() >= 5 or jpholiday.is_holiday(date):

            st.session_state[key] = ""

        else:

            st.session_state[key] = members[idx % len(members)]

            idx += 1

if st.sidebar.button("当月クリア"):

    for d in range(1, days + 1):

        st.session_state[
            f"duty_{year}_{month}_{d}"
        ] = ""

        st.session_state[
            f"sch_{year}_{month}_{d}"
        ] = ""



st.sidebar.subheader("対象年月")

year = st.sidebar.selectbox(
    "年",
    list(range(2024, 2036)),
    index=today.year - 2024
)

month = st.sidebar.selectbox(
    "月",
    list(range(1, 13)),
    index=today.month - 1
)

days = calendar.monthrange(year, month)[1]

next_y, next_m = next_month_info(year, month)
next_days = calendar.monthrange(next_y, next_m)[1]

data_file = f"data_{year}_{month}.json"

st.sidebar.selectbox(
    "安全当番",
    members,
    key=f"safe_{year}_{month}"
)

st.sidebar.multiselect(
    "灯油管理",
    members,
    max_selections=3,
    key=f"oil_{year}_{month}"
)

st.sidebar.multiselect(
    "試料整理",
    members,
    max_selections=3,
    key=f"sample_{year}_{month}"
)

st.sidebar.multiselect(
    "容器整理",
    members,
    max_selections=3,
    key=f"container_{year}_{month}"
)

# =========================
# CSV読込
# =========================
uploaded = st.file_uploader(
    "CSV読込",
    type="csv"
)

if uploaded is not None:

    df_in = pd.read_csv(uploaded)

    for _, row in df_in.iterrows():

        d = int(row["日"])

        if 1 <= d <= days:

            st.session_state[
                f"duty_{year}_{month}_{d}"
            ] = (
                ""
                if pd.isna(row["当番"])
                else str(row["当番"])
            )

            st.session_state[
                f"sch_{year}_{month}_{d}"
            ] = (
                ""
                if pd.isna(row["予定"])
                else str(row["予定"])
            )

    st.success("CSVを読み込みました")

# =========================
# 行描画
# =========================
def draw(d, y, m):

    c1, c2, c3 = st.columns([1, 3, 14])

   
with c1:

    mark = ""

    if datetime.date(y, m, d) == datetime.date.today():
        mark = "★"

    st.markdown(
        f"<div style='color:{get_color_month(d,y,m)};"
        f"font-size:22px'>{d}{mark}</div>",
        unsafe_allow_html=True
    )


    with c2:

        st.text_input(
            "",
            key=f"duty_{y}_{m}_{d}",
            placeholder="当番"
        )

    with c3:

        st.text_area(
            "",
            key=f"sch_{y}_{m}_{d}",
            placeholder="予定",
            height=50
        )

# =========================
# 2か月表示
# =========================

# ---------- 当月 ----------
safe = st.session_state.get(
    f"safe_{year}_{month}",
    ""
)

oil = "・".join(
    st.session_state.get(
        f"oil_{year}_{month}",
        []
    )
)

sample = "・".join(
    st.session_state.get(
        f"sample_{year}_{month}",
        []
    )
)


container = "・".join(
    st.session_state.get(
        f"container_{year}_{month}",
        []
    )
)

st.markdown(
    f"""
    <div style="font-size:36px;font-weight:bold;">
        {year}年{month}月
        &nbsp;&nbsp;&nbsp;&nbsp;
        安全当番：{safe}
    </div>

    <div style="font-size:20px;margin-bottom:10px;">
        灯油管理：{oil}
        &nbsp;&nbsp;&nbsp;&nbsp;
        試料整理：{sample}
        &nbsp;&nbsp;&nbsp;&nbsp;
        容器整理：{container}
    </div>
    """,
    unsafe_allow_html=True
)


left, right = st.columns([1, 1])

with left:
    for d in range(1, min(16, days + 1)):
        draw(d, year, month)

with right:
    for d in range(16, days + 1):
        draw(d, year, month)

st.divider()

# ---------- 翌月 ----------
safe2 = st.session_state.get(
    f"safe_{next_y}_{next_m}",
    ""
)

oil2 = "・".join(
    st.session_state.get(
        f"oil_{next_y}_{next_m}",
        []
    )
)

sample2 = "・".join(
    st.session_state.get(
        f"sample_{next_y}_{next_m}",
        []
    )
)

container2 = "・".join(
    st.session_state.get(
        f"container_{next_y}_{next_m}",
        []
    )
)

st.markdown(
    f"""
    <div style="font-size:24px;font-weight:bold;">
        {next_y}年{next_m}月
        &nbsp;&nbsp;&nbsp;&nbsp;
        安全当番：{safe2}
    </div>

    <div style="font-size:14px;margin-bottom:10px;">
        灯油管理：{oil2}
        &nbsp;&nbsp;&nbsp;&nbsp;
        試料整理：{sample2}
        &nbsp;&nbsp;&nbsp;&nbsp;
        容器整理：{container2}
    </div>
    """,
    unsafe_allow_html=True
)

left, right = st.columns([1, 1])

with left:
    for d in range(1, min(16, next_days + 1)):
        draw(d, next_y, next_m)

with right:
    for d in range(16, next_days + 1):
        draw(d, next_y, next_m)
  
# =========================
# CSV保存
# =========================
df = pd.DataFrame({
    "日": list(range(1, days + 1)),
    "当番": [
        st.session_state[
            f"duty_{year}_{month}_{d}"
        ]
        for d in range(1, days + 1)
    ],
    "予定": [
        st.session_state[
            f"sch_{year}_{month}_{d}"
        ]
        for d in range(1, days + 1)
    ]
})

csv = df.to_csv(
    index=False
).encode("utf-8-sig")

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
    k: v
    for k, v in st.session_state.items()
    if (
        k.startswith("duty_")
        or k.startswith("sch_")
        or k.startswith("safe_")
        or k.startswith("oil_")
        or k.startswith("sample_")
        or k.startswith("container_")
    )
}


with open(
    data_file,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        save_data,
        f,
        ensure_ascii=False,
        indent=2
    )
