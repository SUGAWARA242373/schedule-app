import calendar
import datetime
import io
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
    layout="wide",
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
    """日本時間の本日の日付を取得する。"""
    return datetime.datetime.now(JST).date()


today = get_jst_today()


# =========================================================
# 月計算
# =========================================================
def prev_month_info(year, month):
    """ひとつ前の年月を返す。"""
    if month == 1:
        return year - 1, 12

    return year, month - 1


def next_month_info(year, month):
    """ひとつ後の年月を返す。"""
    if month == 12:
        return year + 1, 1

    return year, month + 1


# =========================================================
# 日付色
# =========================================================
def get_color_month(day, year, month):
    """土曜日、日曜日、祝日に応じた表示色を返す。"""
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
    """保存対象となるsession_stateのキーを判定する。"""
    target_prefixes = (
        "duty_",
        "sch_",
        "safe_",
        "oil_",
        "sample_",
        "container_",
    )

    return str(key).startswith(target_prefixes)


# =========================================================
# 全データCSV作成
# =========================================================
def create_all_data_csv():
    """
    session_state内の保存対象データをCSVへ変換する。

    value_json列には、文字列、リスト、Noneなどを保持するため、
    各値をJSON文字列として格納する。
    """
    rows = []

    for key, value in st.session_state.items():
        if is_schedule_key(key):
            rows.append(
                {
                    "key": key,
                    "value_json": json.dumps(
                        value,
                        ensure_ascii=False,
                    ),
                }
            )

    rows.sort(key=lambda row: row["key"])

    output = io.StringIO()

    writer_df = pd.DataFrame(
        rows,
        columns=[
            "key",
            "value_json",
        ],
    )

    writer_df.to_csv(
        output,
        index=False,
    )

    return output.getvalue().encode("utf-8-sig")


# =========================================================
# 全データCSV読込み
# =========================================================
def load_all_data_csv(uploaded_file):
    """
    全データCSVからスケジュールデータをsession_stateへ復元する。
    CSV内部の値がJSON形式でも通常文字列でも読み込めるようにする。
    """

    # Streamlit UploadedFile を先頭に戻す
    uploaded_file.seek(0)

    # バイトデータとして取得
    raw_data = uploaded_file.read()

    # UTF-8 BOM付き / BOMなし両方に対応
    try:
        text_data = raw_data.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text_data = raw_data.decode("cp932")
        except UnicodeDecodeError:
            text_data = raw_data.decode(
                "utf-8",
                errors="replace"
            )

    # CSV読込み
    loaded_df = pd.read_csv(
        io.StringIO(text_data),
        dtype=str,
        keep_default_na=False,
    )

    # 列名の余分な空白を除去
    loaded_df.columns = [
        str(column).strip()
        for column in loaded_df.columns
    ]

    required_columns = {
        "key",
        "value_json",
    }

    if not required_columns.issubset(
        loaded_df.columns
    ):
        raise ValueError(
            "保存ファイルの形式が正しくありません。"
            "必要な列：key, value_json / "
            f"実際の列：{list(loaded_df.columns)}"
        )

    loaded_count = 0
    skipped_count = 0

    for _, row in loaded_df.iterrows():

        key = str(
            row.get("key", "")
        ).strip()

        value_text = str(
            row.get("value_json", "")
        ).strip()

        # 空キーを無視
        if not key:
            skipped_count += 1
            continue

        # スケジュールキー以外は無視
        if not is_schedule_key(key):
            skipped_count += 1
            continue

        # -----------------------------
        # 値の復元
        # -----------------------------
        try:
            value = json.loads(value_text)

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            # JSONとして読めなくても
            # 通常の文字列として読み込む
            value = value_text

        # -----------------------------
        # safe_
        # -----------------------------
        if key.startswith("safe_"):

            if value in (
                "",
                "None",
                "null",
            ):
                value = None

            elif value not in members:
                value = None

        # -----------------------------
        # multiselect系
        # -----------------------------
        elif key.startswith(
            (
                "oil_",
                "sample_",
                "container_",
            )
        ):

            if isinstance(value, list):

                value = [
                    member
                    for member in value
                    if member in members
                ]

            elif value in (
                "",
                "None",
                "null",
            ):

                value = []

            else:
                # 念のため文字列から復旧
                value = [
                    item.strip()
                    for item in str(value).split(",")
                    if item.strip() in members
                ]

        # -----------------------------
        # duty / schedule
        # -----------------------------
        elif key.startswith(
            (
                "duty_",
                "sch_",
            )
        ):

            if value is None:
                value = ""

            else:
                value = str(value)

        st.session_state[key] = value

        loaded_count += 1

    return loaded_count, skipped_count


# =========================================================
# 前月へ移動
# =========================================================
def move_previous_month():
    year = int(st.session_state["selected_year"])
    month = int(st.session_state["selected_month"])

    previous_year, previous_month = prev_month_info(
        year,
        month,
    )

    st.session_state["selected_year"] = previous_year
    st.session_state["selected_month"] = previous_month


# =========================================================
# 翌月へ移動
# =========================================================
def move_next_month():
    year = int(st.session_state["selected_year"])
    month = int(st.session_state["selected_month"])

    following_year, following_month = next_month_info(
        year,
        month,
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

if st.session_state["selected_month"] not in range(1, 13):
    st.session_state["selected_month"] = today.month


st.sidebar.selectbox(
    "年",
    year_list,
    key="selected_year",
)

st.sidebar.selectbox(
    "月",
    list(range(1, 13)),
    key="selected_month",
)


year = int(st.session_state["selected_year"])
month = int(st.session_state["selected_month"])

days = calendar.monthrange(
    year,
    month,
)[1]

next_y, next_m = next_month_info(
    year,
    month,
)

next_days = calendar.monthrange(
    next_y,
    next_m,
)[1]


# =========================================================
# 前月・翌月ボタン
# =========================================================
button_left, button_right = st.sidebar.columns(2)

with button_left:
    st.button(
        "前月",
        use_container_width=True,
        on_click=move_previous_month,
    )

with button_right:
    st.button(
        "翌月",
        use_container_width=True,
        on_click=move_next_month,
    )


# =========================================================
# State初期化
# =========================================================
def initialize_month_state(target_year, target_month):
    """指定年月の入力項目を初期化する。"""
    target_days = calendar.monthrange(
        target_year,
        target_month,
    )[1]

    for day in range(1, target_days + 1):
        st.session_state.setdefault(
            f"duty_{target_year}_{target_month}_{day}",
            "",
        )

        st.session_state.setdefault(
            f"sch_{target_year}_{target_month}_{day}",
            "",
        )

    # 安全当番
    st.session_state.setdefault(
        f"safe_{target_year}_{target_month}",
        None,
    )

    # 灯油管理
    st.session_state.setdefault(
        f"oil_{target_year}_{target_month}",
        [],
    )

    # 試料整理
    st.session_state.setdefault(
        f"sample_{target_year}_{target_month}",
        [],
    )

    # 容器整理
    st.session_state.setdefault(
        f"container_{target_year}_{target_month}",
        [],
    )


# 当月、翌月を初期化
initialize_month_state(
    year,
    month,
)

initialize_month_state(
    next_y,
    next_m,
)


# =========================================================
# 安全当番データ補正
# =========================================================
def normalize_safe_value(target_year, target_month):
    """安全当番の値を選択可能な形式へ補正する。"""
    key = f"safe_{target_year}_{target_month}"
    value = st.session_state.get(key)

    if value == "":
        st.session_state[key] = None

    elif value is not None and value not in members:
        st.session_state[key] = None


# =========================================================
# 複数選択データ補正
# =========================================================
def normalize_multiselect_value(prefix, target_year, target_month):
    """
    multiselect用データを補正する。

    メンバー一覧に存在しない値を取り除く。
    """
    key = f"{prefix}_{target_year}_{target_month}"
    value = st.session_state.get(key, [])

    if not isinstance(value, list):
        st.session_state[key] = []
        return

    st.session_state[key] = [
        member
        for member in value
        if member in members
    ]


normalize_safe_value(
    year,
    month,
)

normalize_safe_value(
    next_y,
    next_m,
)

for prefix in (
    "oil",
    "sample",
    "container",
):
    normalize_multiselect_value(
        prefix,
        year,
        month,
    )

    normalize_multiselect_value(
        prefix,
        next_y,
        next_m,
    )


# =========================================================
# タイトル
# =========================================================
st.info(
    "入力内容はブラウザのセッション中保持されます。"
    "長期保存する場合は、画面下部の"
    "「すべての入力内容を保存」から"
    "全データCSVをPCへ保存してください。"
)

st.markdown(
    """
    <div style="font-size:40px;font-weight:800;">
        品質管理チーム月間スケジュール表
    </div>
    """,
    unsafe_allow_html=True,
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
    unsafe_allow_html=True,
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
    step=1,
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
    templates,
)


# =========================================================
# テンプレ入力
# =========================================================
if st.sidebar.button("テンプレ入力") and temp:
    key = f"sch_{year}_{month}_{int(day_sel)}"

    current_value = st.session_state.get(
        key,
        "",
    )

    if str(current_value).strip() == "":
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
    members,
)

if st.sidebar.button(
    "当番自動割当（平日のみ）"
):
    member_index = members.index(start)

    for day in range(1, days + 1):
        target_date = datetime.date(
            year,
            month,
            day,
        )

        key = f"duty_{year}_{month}_{day}"

        if (
            target_date.weekday() >= 5
            or jpholiday.is_holiday(target_date)
        ):
            st.session_state[key] = ""

        else:
            st.session_state[key] = members[
                member_index % len(members)
            ]

            member_index += 1

    st.session_state["operation_message"] = (
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

    st.session_state["operation_message"] = (
        "当月の日別データをクリアしました。"
    )

    st.rerun()


# =========================================================
# 月間担当をクリア
# =========================================================
if st.sidebar.button(
    "当月の月間担当をクリア"
):
    st.session_state[
        f"safe_{year}_{month}"
    ] = None

    st.session_state[
        f"oil_{year}_{month}"
    ] = []

    st.session_state[
        f"sample_{year}_{month}"
    ] = []

    st.session_state[
        f"container_{year}_{month}"
    ] = []

    st.session_state["operation_message"] = (
        "当月の月間担当をクリアしました。"
    )

    st.rerun()


# =========================================================
# 操作メッセージ表示
# =========================================================
operation_message = st.session_state.pop(
    "operation_message",
    None,
)

if operation_message:
    st.success(operation_message)


# =========================================================
# 月間担当
# =========================================================
st.sidebar.subheader("月間担当")

st.sidebar.selectbox(
    "安全当番",
    members,
    index=None,
    placeholder="選択してください",
    key=f"safe_{year}_{month}",
)

st.sidebar.multiselect(
    "灯油管理",
    members,
    max_selections=3,
    key=f"oil_{year}_{month}",
)

st.sidebar.multiselect(
    "試料整理",
    members,
    max_selections=3,
    key=f"sample_{year}_{month}",
)

st.sidebar.multiselect(
    "容器整理",
    members,
    max_selections=3,
    key=f"container_{year}_{month}",
)


# =========================================================
# 全期間CSVデータ読込
# =========================================================
st.sidebar.divider()

st.sidebar.subheader(
    "全入力データ読込"
)

uploaded_all_data = st.sidebar.file_uploader(
    "schedule_all_data.csvを選択",
    type=["csv"],
    key="all_data_csv_uploader",
    help=(
        "「すべての入力内容を保存」で"
        "ダウンロードしたCSVファイルを選択してください。"
    ),
)


if uploaded_all_data is not None:
    upload_id = (
        uploaded_all_data.name,
        uploaded_all_data.size,
    )

    if (
        st.session_state.get(
            "last_uploaded_all_data"
        )
        != upload_id
    ):
        try:
            loaded_count, skipped_count = load_all_data_csv(
                uploaded_all_data
            )

            st.session_state[
                "last_uploaded_all_data"
            ] = upload_id

            st.session_state[
                "operation_message"
            ] = (
                f"全期間の保存データを"
                f"{loaded_count}件読み込みました。"
                f"（スキップ：{skipped_count}件）"
            )

            st.rerun()

        except Exception as error:
            st.sidebar.error(
                "全入力データの読込みに失敗しました。"
                f"詳細: {error}"
            )
# =========================================================
# 当月CSV読込み
# =========================================================
st.sidebar.divider()

st.sidebar.subheader(
    "当月データ読込"
)

uploaded_csv = st.sidebar.file_uploader(
    "当月CSVを選択",
    type=["csv"],
    key="monthly_csv_uploader",
    help=(
        "「当月CSVダウンロード」で"
        "保存したCSVを選択してください。"
    ),
)


if uploaded_csv is not None:
    upload_id = (
        uploaded_csv.name,
        uploaded_csv.size,
    )

    if (
        st.session_state.get(
            "last_uploaded_monthly_csv"
        )
        != upload_id
    ):
        try:
            df_in = pd.read_csv(
                uploaded_csv,
                encoding="utf-8-sig",
            )

            required_columns = {
                "日",
                "当番",
                "予定",
            }

            if not required_columns.issubset(
                df_in.columns
            ):
                st.sidebar.error(
                    "当月CSVには"
                    "「日」「当番」「予定」の"
                    "3列が必要です。"
                )

            else:
                loaded_count = 0

                for _, row in df_in.iterrows():
                    if pd.isna(row["日"]):
                        continue

                    try:
                        day = int(row["日"])

                    except (TypeError, ValueError):
                        continue

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

                        loaded_count += 1

                st.session_state[
                    "last_uploaded_monthly_csv"
                ] = upload_id

                st.session_state[
                    "operation_message"
                ] = (
                    f"当月データを"
                    f"{loaded_count}日分読み込みました。"
                )

                st.rerun()

        except Exception as error:
            st.sidebar.error(
                "当月CSVの読込みに失敗しました。"
                f"詳細: {error}"
            )


# =========================================================
# 行描画
# =========================================================
def draw(
    day,
    target_year,
    target_month,
):
    column_day, column_duty, column_schedule = (
        st.columns([1, 3, 14])
    )

    target_date = datetime.date(
        target_year,
        target_month,
        day,
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
            target_month,
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
            unsafe_allow_html=True,
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
            label_visibility="collapsed",
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
            label_visibility="collapsed",
        )


# =========================================================
# 月間担当取得
# =========================================================
def get_monthly_assignment(
    target_year,
    target_month,
):
    safe_value = st.session_state.get(
        f"safe_{target_year}_{target_month}"
    )

    safe_text = (
        safe_value
        if safe_value
        else "未選択"
    )

    oil_value = st.session_state.get(
        f"oil_{target_year}_{target_month}",
        [],
    )

    sample_value = st.session_state.get(
        f"sample_{target_year}_{target_month}",
        [],
    )

    container_value = st.session_state.get(
        f"container_{target_year}_{target_month}",
        [],
    )

    oil_text = "・".join(
        oil_value
        if isinstance(oil_value, list)
        else []
    )

    sample_text = "・".join(
        sample_value
        if isinstance(sample_value, list)
        else []
    )

    container_text = "・".join(
        container_value
        if isinstance(container_value, list)
        else []
    )

    return (
        safe_text,
        oil_text,
        sample_text,
        container_text,
    )


# =========================================================
# 当月表示
# =========================================================
safe, oil, sample, container = (
    get_monthly_assignment(
        year,
        month,
    )
)

st.markdown(
    f"""
    <div style="
        font-size:28px;
        font-weight:700;
        margin-top:20px;
    ">
        {year}年 {month}月
    </div>

    <div style="
        font-size:20px;
        margin-bottom:10px;
    ">
        安全当番：{safe}
        &nbsp;&nbsp;&nbsp;&nbsp;

        灯油管理：{oil if oil else "未選択"}
        &nbsp;&nbsp;&nbsp;&nbsp;

        試料整理：{sample if sample else "未選択"}
        &nbsp;&nbsp;&nbsp;&nbsp;

        容器整理：{container if container else "未選択"}
    </div>
    """,
    unsafe_allow_html=True,
)


left, right = st.columns([1, 1])

with left:
    for day in range(
        1,
        min(16, days + 1),
    ):
        draw(
            day,
            year,
            month,
        )

with right:
    for day in range(
        16,
        days + 1,
    ):
        draw(
            day,
            year,
            month,
        )


# =========================================================
# 翌月表示
# =========================================================
st.divider()

safe2, oil2, sample2, container2 = (
    get_monthly_assignment(
        next_y,
        next_m,
    )
)

st.markdown(
    f"""
    <div style="
        font-size:28px;
        font-weight:700;
    ">
        {next_y}年 {next_m}月
    </div>

    <div style="
        font-size:14px;
        margin-bottom:10px;
    ">
        安全当番：{safe2}
        &nbsp;&nbsp;&nbsp;&nbsp;

        灯油管理：{oil2 if oil2 else "未選択"}
        &nbsp;&nbsp;&nbsp;&nbsp;

        試料整理：{sample2 if sample2 else "未選択"}
        &nbsp;&nbsp;&nbsp;&nbsp;

        容器整理：{container2 if container2 else "未選択"}
    </div>
    """,
    unsafe_allow_html=True,
)


left, right = st.columns([1, 1])

with left:
    for day in range(
        1,
        min(16, next_days + 1),
    ):
        draw(
            day,
            next_y,
            next_m,
        )

with right:
    for day in range(
        16,
        next_days + 1,
    ):
        draw(
            day,
            next_y,
            next_m,
        )


# =========================================================
# ダウンロード
# =========================================================
st.divider()

st.subheader("データ保存")


# =========================================================
# 当月CSV作成
# =========================================================
monthly_df = pd.DataFrame(
    {
        "日": list(
            range(1, days + 1)
        ),

        "当番": [
            st.session_state.get(
                f"duty_{year}_{month}_{day}",
                "",
            )
            for day in range(
                1,
                days + 1,
            )
        ],

        "予定": [
            st.session_state.get(
                f"sch_{year}_{month}_{day}",
                "",
            )
            for day in range(
                1,
                days + 1,
            )
        ],
    }
)

monthly_csv = monthly_df.to_csv(
    index=False,
).encode("utf-8-sig")


# =========================================================
# 全期間CSV作成
# =========================================================
all_data_csv = create_all_data_csv()


# =========================================================
# ダウンロードボタン
# =========================================================
download_left, download_right = st.columns(2)

with download_left:
    st.download_button(
        label="当月CSVダウンロード",
        data=monthly_csv,
        file_name=(
            f"schedule_{year}_{month:02d}.csv"
        ),
        mime="text/csv",
        use_container_width=True,
    )

with download_right:
    st.download_button(
        label="すべての入力内容を保存",
        data=all_data_csv,
        file_name="schedule_all_data.csv",
        mime="text/csv",
        use_container_width=True,
    )


st.caption(
    "「すべての入力内容を保存」では、"
    "これまで画面上で入力した全期間の当番、予定、"
    "安全当番、灯油管理、試料整理、容器整理を"
    "schedule_all_data.csvへ保存します。"
)
