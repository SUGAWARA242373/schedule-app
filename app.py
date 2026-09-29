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
    date_value = datetime.date(
        year,
        month,
        day,
    )

    if date_value.weekday() == 5:
        return "blue"

    if date_value.weekday() == 6:
        return "red"

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
    session_state内の全期間データをCSVへ変換する。

    value_json列には文字列、リスト、Noneなどを
    JSON文字列として格納する。
    """
    rows = []

    for key, value in st.session_state.items():
        if is_schedule_key(key):
            rows.append(
                {
                    "key": str(key),
                    "value_json": json.dumps(
                        value,
                        ensure_ascii=False,
                    ),
                }
            )

    rows.sort(
        key=lambda row: row["key"]
    )

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
        lineterminator="\n",
    )

    return output.getvalue().encode(
        "utf-8-sig"
    )


# =========================================================
# アップロードファイル文字コード判定
# =========================================================
def decode_uploaded_file(raw_data):
    """
    CSVファイルを文字列へ変換する。

    UTF-8、UTF-8 BOM付き、CP932に対応する。
    """
    encodings = (
        "utf-8-sig",
        "utf-8",
        "cp932",
    )

    for encoding in encodings:
        try:
            return raw_data.decode(encoding)

        except UnicodeDecodeError:
            continue

    raise ValueError(
        "CSVファイルの文字コードを判定できませんでした。"
        "UTF-8またはCP932形式のCSVを使用してください。"
    )


# =========================================================
# 全データCSV読込み
# =========================================================
def load_all_data_csv(uploaded_file):
    """
    全データCSVからスケジュールデータを復元する。

    必要な列：
    key
    value_json
    """
    uploaded_file.seek(0)
    raw_data = uploaded_file.getvalue()

    if not raw_data:
        raise ValueError(
            "選択されたCSVファイルは空です。"
        )

    text_data = decode_uploaded_file(
        raw_data
    )

    try:
        loaded_df = pd.read_csv(
            io.StringIO(text_data),
            dtype=str,
            keep_default_na=False,
        )

    except pd.errors.EmptyDataError as error:
        raise ValueError(
            "CSVファイルに読込み可能なデータがありません。"
        ) from error

    except pd.errors.ParserError as error:
        raise ValueError(
            "CSVファイルの行または区切り文字が正しくありません。"
        ) from error

    loaded_df.columns = [
        str(column)
        .replace("\ufeff", "")
        .strip()
        for column in loaded_df.columns
    ]

    required_columns = {
        "key",
        "value_json",
    }

    if not required_columns.issubset(
        set(loaded_df.columns)
    ):
        raise ValueError(
            "保存ファイルの形式が正しくありません。"
            "「すべての入力内容を保存」で作成した"
            "schedule_all_data.csvを選択してください。"
            f" 必要な列：key, value_json"
            f" / 実際の列：{list(loaded_df.columns)}"
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

        if not key:
            skipped_count += 1
            continue

        if not is_schedule_key(key):
            skipped_count += 1
            continue

        try:
            value = json.loads(
                value_text
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            value = value_text

        # 安全当番
        if key.startswith("safe_"):
            if value in (
                "",
                "None",
                "null",
                None,
            ):
                value = None

            elif value not in members:
                value = None

        # 複数選択項目
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
                None,
            ):
                value = []

            else:
                value = [
                    item.strip()
                    for item in str(value).split(",")
                    if item.strip() in members
                ]

        # 当番、予定
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
# 当月CSV読込み
# =========================================================
def load_monthly_csv(
    uploaded_file,
    year,
    month,
    days,
):
    """
    当月CSVから日別の当番と予定を復元する。
    """
    uploaded_file.seek(0)
    raw_data = uploaded_file.getvalue()

    if not raw_data:
        raise ValueError(
            "選択されたCSVファイルは空です。"
        )

    text_data = decode_uploaded_file(
        raw_data
    )

    try:
        loaded_df = pd.read_csv(
            io.StringIO(text_data),
            dtype=str,
            keep_default_na=False,
        )

    except pd.errors.EmptyDataError as error:
        raise ValueError(
            "CSVファイルに読込み可能なデータがありません。"
        ) from error

    except pd.errors.ParserError as error:
        raise ValueError(
            "CSVファイルの行または区切り文字が正しくありません。"
        ) from error

    loaded_df.columns = [
        str(column)
        .replace("\ufeff", "")
        .strip()
        for column in loaded_df.columns
    ]

    required_columns = {
        "日",
        "当番",
        "予定",
    }

    if not required_columns.issubset(
        set(loaded_df.columns)
    ):
        raise ValueError(
            "当月CSVの形式が正しくありません。"
            "必要な列は「日」「当番」「予定」です。"
            f" 実際の列：{list(loaded_df.columns)}"
        )

    loaded_count = 0
    skipped_count = 0

    for _, row in loaded_df.iterrows():
        day_text = str(
            row.get("日", "")
        ).strip()

        try:
            day = int(
                float(day_text)
            )

        except (
            TypeError,
            ValueError,
        ):
            skipped_count += 1
            continue

        if not 1 <= day <= days:
            skipped_count += 1
            continue

        duty_value = str(
            row.get("当番", "")
        )

        schedule_value = str(
            row.get("予定", "")
        )

        st.session_state[
            f"duty_{year}_{month}_{day}"
        ] = duty_value

        st.session_state[
            f"sch_{year}_{month}_{day}"
        ] = schedule_value

        loaded_count += 1

    return loaded_count, skipped_count


# =========================================================
# 年月State初期化
# =========================================================
st.session_state.setdefault(
    "selected_year",
    today.year,
)

st.session_state.setdefault(
    "selected_month",
    today.month,
)


# =========================================================
# 前月へ移動
# =========================================================
def move_previous_month():
    current_year = int(
        st.session_state["selected_year"]
    )

    current_month = int(
        st.session_state["selected_month"]
    )

    previous_year, previous_month = (
        prev_month_info(
            current_year,
            current_month,
        )
    )

    st.session_state[
        "selected_year"
    ] = previous_year

    st.session_state[
        "selected_month"
    ] = previous_month


# =========================================================
# 翌月へ移動
# =========================================================
def move_next_month():
    current_year = int(
        st.session_state["selected_year"]
    )

    current_month = int(
        st.session_state["selected_month"]
    )

    following_year, following_month = (
        next_month_info(
            current_year,
            current_month,
        )
    )

    st.session_state[
        "selected_year"
    ] = following_year

    st.session_state[
        "selected_month"
    ] = following_month


# =========================================================
# サイドバー 年月選択
# =========================================================
st.sidebar.subheader(
    "対象年月"
)

year_list = list(
    range(2024, 2036)
)

if (
    st.session_state["selected_year"]
    not in year_list
):
    st.session_state[
        "selected_year"
    ] = today.year

if (
    st.session_state["selected_month"]
    not in range(1, 13)
):
    st.session_state[
        "selected_month"
    ] = today.month


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
