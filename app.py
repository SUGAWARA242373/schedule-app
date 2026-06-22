import streamlit as st
import pandas as pd
import calendar
import datetime

st.set_page_config(layout="wide")

# 年月
year = st.number_input("年", value=2026)
month = st.number_input("月", 1, 12, 6)
days = calendar.monthrange(year, month)[1]
today = datetime.date.today()

st.markdown(
    f"""
    <div style="font-size:40px;font-weight:800;">品質管理チーム月間スケジュール表</div>
    <div style="font-size:32px;margin-bottom:20px;">{year}年 {month}月</div>
    """,
    unsafe_allow_html=True
)

# widget state だけを使う
for d in range(1, days + 1):
    st.session_state.setdefault(f"duty_{d}", "")
    st.session_state.setdefault(f"sch_{d}", "")

def draw(d):
    c1, c2, c3 = st.columns([1, 2, 6])

    with c1:
        mark = "★" if datetime.date(year, month, d) == today else ""
        st.markdown(f"<b>{d}{mark}</b>", unsafe_allow_html=True)

    with c2:
        st.text_input("", key=f"duty_{d}", placeholder="当番")

    with c3:
        st.text_area("", key=f"sch_{d}", placeholder="予定", height=50)

colL, colR = st.columns(2)
with colL:
    for d in range(1, min(16, days + 1)):
        draw(d)
with colR:
    for d in range(16, days + 1):
        draw(d)

# =========================
# CSV保存（★ここだけ追加）
# =========================
st.markdown("---")
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



 =========================
uploaded = st.file_uploader("CSV読込", type="csv", key="csv_upload")

if uploaded and "csv_loaded" not in st.session_state:
    df_in = pd.read_csv(uploaded)

    st.session_state["_csv_buffer"] = df_in
    st.session_state["csv_loaded"] = True
    st.rerun()

if st.session_state.get("csv_loaded", False):
    df_in = st.session_state.pop("_csv_buffer")
    st.session_state.pop("csv_loaded", None)

    for _, row in df_in.iterrows():
        d = int(row["日"])
        if 1 <= d <= days:
            st.session_state[f"duty_{d}"] = "" if pd.isna(row["当番"]) else str(row["当番"])
            st.session_state[f"sch_{d}"] = "" if pd.isna(row["予定"]) else str(row["予定"])

    st.success("CSVを読み込みました")
    st.rerun()


# =========================
# CSV保存・読込
# =========================
if st.button("CSV保存"):
    df = pd.DataFrame({
        "日": list(range(1, days + 1)),
        "当番": [st.session_state[f"duty_{d}"] for d in range(1, days + 1)],
        "予定": [st.session_state[f"sch_{d}"] for d in range(1, days + 1)],
    })
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("CSVダウンロード", csv, f"schedule_{year}_{month}.csv", "text/csv")

uploaded = st.file_uploader("CSV読込", type="csv")
if uploaded:
    df_in = pd.read_csv(uploaded)
    for _, row in df_in.iterrows():
        d = int(row["日"])
        if 1 <= d <= days:
            st.session_state[f"duty_{d}"] = "" if pd.isna(row["当番"]) else str(row["当番"])
            st.session_state[f"sch_{d}"] = "" if pd.isna(row["予定"]) else str(row["予定"])
    st.rerun()

# =========================
# 自動保存（widget stateのみ）
# =========================
save_data = {k: v for k, v in st.session_state.items() if k.startswith("duty_") or k.startswith("sch_")}
with open(data_file, "w", encoding="utf-8") as f:
    json.dump(save_data, f, ensure_ascii=False, indent=2)
