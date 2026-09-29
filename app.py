import calendar
import datetime
import json
from zoneinfo import ZoneInfo

import jpholiday
import pandas as pd
import streamlit as st


# =========================================================
# 基本設定
# =========================================================
st.set_page_config(
    page_title="品質管理チーム月間スケジュール表",
    layout="wide"
)

JST = ZoneInfo("Asia/Tokyo")


# =========================================================
# メンバー
# =========================================================
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
    "藤田",
]


# =========================================================
# 日本時間取得
# =========================================================
def get_jst_today():
    return datetime.datetime.now(JST).date()


today = get_jst_today()


# =========================================================
# 月計算
# =========================================================
def prev_month_info(year, month):
    if month == 1:
        return year - 1, 12
    return year, month - 1


def next_month_info(year, month):
    if month == 12:
        return year + 1, 1
    return year, month + 1


# =========================================================
# 日付色
# =========================================================
def get_color_month(day, year, month):
    date_value = datetime.date(year, month, day)

    # 土曜日
    if date_value.weekday() == 5:
        return "blue"

    # 日曜日
    if date_value.weekday() == 6:
        return "red"

    # 祝日
    if jpholiday.is_holiday(date_value):
        return "red"

    return "black"


# =========================================================
# 保存対象キー判定
# =========================================================
def is_schedule_key(key):
    target_prefixes = (
        "duty_",
        "sch_",
        "safe_",
        "oil_",
        "sample_",
        "container_",
    )

    return key.startswith(target_prefixes)


# =========================================================
# 年月セッション初期化
# =========================================================
st.session_state.setdefault(
    "selected_year",
    today.year
)

st.session_state.setdefault(
    "selected_month",
    today.month
)


# =========================================================
# 前月へ移動
# =========================================================
def move_previous_month():
    year = st.session_state["selected_year"]
    month = st.session_state["selected_month"]

    previous_year, previous_month = prev_month_info(
        year,
        month
    )

    st.session_state["selected_year"] = previous_year
    st.session_state["selected_month"] = previous_month


# =========================================================
# 翌月へ移動
# =========================================================
def move_next_month():
    year = st.session_state["selected_year"]
    month = st.session_state["selected_month"]

    following_year, following_month = next_month_info(
        year,
        month
    )

    st.session_state["selected_year"] = following_year
    st.session_state["selected_month"] = following_month


# =========================================================
# サイドバー 年月選択
# =========================================================
st.sidebar.subheader("対象年月")

year_list = list(range(2024, 2036))

if st.session_state["selected_year"] not in year_list:
    st.session_state["selected_year"] = today.year


st.sidebar.selectbox(
    "年",
    year_list,
    key="selected_year"
)

st.sidebar.selectbox(
    "月",
    list(range(1, 13)),
    key="selected_month"
)


year = int(st.session_state["selected_year"])
month = int(st.session_state["selected_month"])

days = calendar.monthrange(
    year,
    month
)[1]

next_y, next_m = next_month_info(
    year,
    month
)

next_days = calendar.monthrange(
    next_y,
    next_m
)[1]


# =========================================================
# 前月・翌月ボタン
# =========================================================
button_left, button_right = st.sidebar.columns(2)

with button_left:
    st.button(
        "前月",
        use_container_width=True,
        on_click=move_previous_month
    )

with button_right:
    st.button(
        "翌月",
        use_container_width=True,
        on_click=move_next_month
    )


# =========================================================
# State初期化
# =========================================================
def initialize_month_state(target_year, target_month):

    target_days = calendar.monthrange(
        target_year,
        target_month
    )[1]

    for day in range(1, target_days + 1):

        st.session_state.setdefault(
            f"duty_{target_year}_{target_month}_{day}",
            ""
        )

        st.session_state.setdefault(
            f"sch_{target_year}_{target_month}_{day}",
            ""
        )

    # 安全当番
    st.session_state.setdefault(
        f"safe_{target_year}_{target_month}",
        None
    )

    # 灯油管理
    st.session_state.setdefault(
        f"oil_{target_year}_{target_month}",
        []
    )

    # 試料整理
    st.session_state.setdefault(
        f"sample_{target_year}_{target_month}",
        []
    )

    # 容器整理
    st.session_state.setdefault(
        f"container_{target_year}_{target_month}",
        []
    )


# 当月、翌月を初期化
initialize_month_state(
    year,
    month
)

initialize_month_state(
    next_y,
    next_m
)


# =========================================================
# 安全当番データ補正
# =========================================================
def normalize_safe_value(target_year, target_month):

    key = f"safe_{target_year}_{target_month}"
    value = st.session_state.get(key)

    if value == "":
        st.session_state[key] = None

    elif value is not None and value not in members:
        st.session_state[key] = None


normalize_safe_value(
    year,
    month
)

normalize_safe_value(
    next_y,
    next_m
)


# =========================================================
# タイトル
# =========================================================
st.info(
    "入力内容はブラウザのセッション中保持されます。"
    "長期保存する場合は「すべての入力内容を保存」から"
    "JSONファイルをPCへ保存してください。"
)

st.markdown(
    """
    <div style="font-size:40px;font-weight:800;">
        品質管理チーム月間スケジュール表
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# CSS
# =========================================================
st.markdown(
    """
    <style>

    div[data-testid="stTextInput"] input {
        height: 48px !important;
        font-size: 14px !important;
    }

    div[data-testid="stTextArea"] textarea {
        min-height: 48px !important;
        font-size: 12px !important;
    }

    .today-mark {
        color: #ff9800;
        font-weight: bold;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# サイドバー操作
# =========================================================
st.sidebar.header("操作")

day_sel = st.sidebar.number_input(
    "日付",
    min_value=1,
    max_value=days,
    value=1,
    step=1
)

templates = [
    "",
    "外船",
    "チーム会議",
    "安全衛生委員会",
    "在庫調査日",
]

temp = st.sidebar.selectbox(
    "予定テンプレ",
    templates
)


# =========================================================
# テンプレ入力
# =========================================================
if st.sidebar.button("テンプレ入力") and temp:

    key = (
        f"sch_{year}_{month}_{int(day_sel)}"
    )

    current_value = st.session_state.get(
        key,
        ""
    )

    if current_value.strip() == "":
        st.session_state[key] = temp

    else:
        st.session_state[key] = (
            f"{current_value} / {temp}"
        )

    st.rerun()


# =========================================================
# 当番自動割当
# =========================================================
start = st.sidebar.selectbox(
    "開始当番（1日）",
    members
)

if st.sidebar.button(
    "当番自動割当（平日のみ）"
):

    member_index = members.index(start)

    for day in range(1, days + 1):

        target_date = datetime.date(
            year,
            month,
            day
        )

        key = (
            f"duty_{year}_{month}_{day}"
        )

        if (
            target_date.weekday() >= 5
            or jpholiday.is_holiday(target_date)
        ):
            st.session_state[key] = ""

        else:
            st.session_state[key] = (
                members[
                    member_index % len(members)
                ]
            )

            member_index += 1

    st.success(
        "当番を自動割当しました。"
    )

    st.rerun()


# =========================================================
# 当月の日別データをクリア
# =========================================================
if st.sidebar.button(
    "当月の日別データをクリア"
):

    for day in range(1, days + 1):

        st.session_state[
            f"duty_{year}_{month}_{day}"
        ] = ""

        st.session_state[
            f"sch_{year}_{month}_{day}"
        ] = ""

    st.success(
        "当月の日別データをクリアしました。"
    )

    st.rerun()


# =========================================================
# 月間担当
# =========================================================
st.sidebar.subheader("月間担当")

st.sidebar.selectbox(
    "安全当番",
    members,
    index=None,
    placeholder="選択してください",
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


# =========================================================
# 保存済みJSONデータ読込
# =========================================================
st.sidebar.divider()

st.sidebar.subheader(
    "保存データ読込"
)

uploaded_json = st.sidebar.file_uploader(
    "schedule_data.jsonを選択",
    type=["json"],
    key="json_uploader"
)


if uploaded_json is not None:

    upload_id = (
        uploaded_json.name,
        uploaded_json.size
    )

    if (
        st.session_state.get(
            "last_uploaded_json"
        )
        != upload_id
    ):

        try:
            loaded_data = json.load(
                uploaded_json
            )

            if not isinstance(
                loaded_data,
                dict
            ):
                st.sidebar.error(
                    "JSONデータの形式が正しくありません。"
                )

            else:

                loaded_count = 0

                for key, value in loaded_data.items():

                    if is_schedule_key(key):
                        st.session_state[key] = value
                        loaded_count += 1

                st.session_state[
                    "last_uploaded_json"
                ] = upload_id

                st.sidebar.success(
                    f"{loaded_count}件のデータを"
                    "読み込みました。"
                )

                st.rerun()

        except Exception as error:

            st.sidebar.error(
                "JSONの読込みに失敗しました。"
                f"詳細: {error}"
            )


# =========================================================
# CSV読込み
# =========================================================
uploaded_csv = st.file_uploader(
    "当月CSV読込",
    type=["csv"],
    key="csv_uploader"
)


if uploaded_csv is not None:

    try:
        df_in = pd.read_csv(
            uploaded_csv
        )

        required_columns = {
            "日",
            "当番",
            "予定"
        }

        if not required_columns.issubset(
            df_in.columns
        ):
            st.error(
                "CSVには「日」「当番」「予定」の"
                "3列が必要です。"
            )

        else:

            upload_id = (
                uploaded_csv.name,
                uploaded_csv.size
            )

            if (
                st.session_state.get(
                    "last_uploaded_csv"
                )
                != upload_id
            ):

                for _, row in df_in.iterrows():

                    day = int(row["日"])

                    if 1 <= day <= days:

                        duty_value = (
                            ""
                            if pd.isna(row["当番"])
                            else str(row["当番"])
                        )

                        schedule_value = (
                            ""
                            if pd.isna(row["予定"])
                            else str(row["予定"])
                        )

                        st.session_state[
                            f"duty_{year}_{month}_{day}"
                        ] = duty_value

                        st.session_state[
                            f"sch_{year}_{month}_{day}"
                        ] = schedule_value

                st.session_state[
                    "last_uploaded_csv"
                ] = upload_id

                st.success(
                    "CSVを読み込みました。"
                )

                st.rerun()

    except Exception as error:

        st.error(
            "CSVの読込みに失敗しました。"
            f"詳細: {error}"
        )


# =========================================================
# 行描画
# =========================================================
def draw(
    day,
    target_year,
    target_month
):

    column_day, column_duty, column_schedule = (
        st.columns([1, 3, 14])
    )

    target_date = datetime.date(
        target_year,
        target_month,
        day
    )

    with column_day:

        mark = (
            "★"
            if target_date == get_jst_today()
            else ""
        )

        color = get_color_month(
            day,
            target_year,
            target_month
        )

        st.markdown(
            (
                f"<div style='"
                f"color:{color};"
                f"font-size:22px;'>"
                f"{day}"
                f"<span class='today-mark'>"
                f"{mark}"
                f"</span>"
                f"</div>"
            ),
            unsafe_allow_html=True
        )

    with column_duty:

        st.text_input(
            "当番",
            key=(
                f"duty_"
                f"{target_year}_"
                f"{target_month}_"
                f"{day}"
            ),
            placeholder="当番",
            label_visibility="collapsed"
        )

    with column_schedule:

        st.text_area(
            "予定",
            key=(
                f"sch_"
                f"{target_year}_"
                f"{target_month}_"
                f"{day}"
            ),
            placeholder="予定",
            height=50,
            label_visibility="collapsed"
        )


# =========================================================
# 月間担当取得
# =========================================================
def get_monthly_assignment(
    target_year,
    target_month
):

    safe_value = st.session_state.get(
        f"safe_{target_year}_{target_month}"
    )

    safe_text = (
        safe_value
        if safe_value
        else "未選択"
    )

    oil_text = "・".join(
        st.session_state.get(
            f"oil_{target_year}_{target_month}",
            []
        )
    )

    sample_text = "・".join(
        st.session_state.get(
            f"sample_{target_year}_{target_month}",
            []
        )
    )

    container_text = "・".join(
        st.session_state.get(
            f"container_{target_year}_{target_month}",
            []
        )
    )

    return (
        safe_text,
        oil_text,
        sample_text,
        container_text
    )


# =========================================================
# 当月表示
# =========================================================
safe, oil, sample, container = (
    get_monthly_assignment(
        year,
        month
    )
)

st.markdown(
    f"""
    <div style="font-size:28px;font-weight:700;
                margin-top:20px;">
        {year}年 {month}月
    </div>

    <div style="font-size:20px;margin-bottom:10px;">
        安全当番：{safe}
        &nbsp;&nbsp;&nbsp;&nbsp;

        灯油管理：{oil if oil else "未選択"}
        &nbsp;&nbsp;&nbsp;&nbsp;

        試料整理：{sample if sample else "未選択"}
        &nbsp;&nbsp;&nbsp;&nbsp;

        容器整理：{container if container else "未選択"}
    </div>
    """,
    unsafe_allow_html=True
)


left, right = st.columns([1, 1])

with left:
    for day in range(
        1,
        min(16, days + 1)
    ):
        draw(
            day,
            year,
            month
        )

with right:
    for day in range(
        16,
        days + 1
    ):
        draw(
            day,
            year,
            month
        )


# =========================================================
# 翌月表示
# =========================================================
st.divider()

safe2, oil2, sample2, container2 = (
    get_monthly_assignment(
        next_y,
        next_m
    )
)

st.markdown(
    f"""
    <div style="font-size:28px;font-weight:700;">
        {next_y}年 {next_m}月
    </div>

    <div style="font-size:14px;margin-bottom:10px;">
        安全当番：{safe2}
        &nbsp;&nbsp;&nbsp;&nbsp;

        灯油管理：{oil2 if oil2 else "未選択"}
        &nbsp;&nbsp;&nbsp;&nbsp;

        試料整理：{sample2 if sample2 else "未選択"}
        &nbsp;&nbsp;&nbsp;&nbsp;

        容器整理：{container2 if container2 else "未選択"}
    </div>
    """,
    unsafe_allow_html=True
)


left, right = st.columns([1, 1])

with left:
    for day in range(
        1,
        min(16, next_days + 1)
    ):
        draw(
            day,
            next_y,
            next_m
        )

with right:
    for day in range(
        16,
        next_days + 1
    ):
        draw(
            day,
            next_y,
            next_m
        )


# =========================================================
# 当月CSVダウンロード
# =========================================================
st.divider()

df = pd.DataFrame(
    {
        "日": list(
            range(1, days + 1)
        ),

        "当番": [
            st.session_state.get(
                f"duty_{year}_{month}_{day}",
                ""
            )
            for day in range(
                1,
                days + 1
            )
        ],

        "予定": [
            st.session_state.get(
                f"sch_{year}_{month}_{day}",
                ""
            )
            for day in range(
                1,
                days + 1
            )
        ],
    }
)


csv = df.to_csv(
    index=False
).encode(
    "utf-8-sig"
)


st.download_button(
    "当月CSVダウンロード",
    data=csv,
    file_name=(
        f"schedule_{year}_{month:02d}.csv"
    ),
    mime="text/csv"
)


# =========================================================
# 全年月データをJSON化
# =========================================================
save_data = {
    key: value
    for key, value in st.session_state.items()
    if is_schedule_key(key)
}


json_data = json.dumps(
    save_data,
    ensure_ascii=False,
    indent=2
)


# =========================================================
# 全入力内容をPCへ保存
# =========================================================
st.download_button(
    label="すべての入力内容を保存",
    data=json_data,
    file_name="schedule_data.json",
    mime="application/json"
)
