import streamlit as st
import pandas as pd
import calendar
import datetime
import json
import os
import jpholiday

# =================================================
# ページ設定 + CSS
# =================================================
st.set_page_config(layout="wide")

st.markdown("""
<style>
input::placeholder { font-size:11px; color:#999; }
input { font-size:13px; }
.scroll-area {
    height:65vh;
    overflow-y:auto;
    border-top:1px solid #ccc;
    padding-top:6px;
}
</style>
""", unsafe_allow_html=True)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# =================================================
# 年月選択
# =================================================
c1, c2 = st.columns([2,1])
with c1:
    year = st.number_input("年", value=2026, step=1)
with c2:
    month = st.number_input("月", 1, 12, 6)

days = calendar.monthrange(year, month)[1]
data_file = f"{DATA_DIR}/data_{year}_{month}.json"

# =================================================
# 月変更検知
# =================================================
if (
    "cy" not in st.session_state
    or st.session_state.cy != year
    or st.session_state.cm != month
):
    st.session_state.clear()
    st.session_state.cy = year
    st.session_state.cm = month
    st.session_state.loaded = False

# =================================================
# データ構造
# =================================================
st.session_state.setdefault("data", {
    "schedule": {},
    "duty": {},
    "month": {}
})

if os.path.exists(data_file) and not st.session_state.loaded:
    with open(data_file, "r", encoding="utf-8") as f:
        st.session_state.data = json.load(f)
    st.session_state.loaded = True

# ★ 必ず補完 ★
st.session_state.data.setdefault("month", {})
st.session_state.data["month"].setdefault("start", "")
st.session_state.data["month"].setdefault("container", [])
st.session_state.data["month"].setdefault("sample", [])
st.session_state.data["month"].setdefault("oil", [])

for d in range(1, days+1):
    st.session_state.data["schedule"].setdefault(str(d), "")
    st.session_state.data["duty"].setdefault(str(d), "")

# =================================================
# タイトル
# =================================================
st.markdown(
    f"<h1 style='font-size:42px'>品質管理チーム 月間スケジュール</h1>"
    f"<h2 style='font-size:30px'>{year}年 {month}月</h2>",
    unsafe_allow_html=True
)

# =================================================
# 月次当番（固定）
# =================================================
ms = st.session_state.data["month"]
st.markdown("### 月次当番")
st.markdown(
    f"""
    <div style='border:1px solid #ddd;padding:8px;border-radius:6px'>
    開始当番：{ms.get("start","")}<br>
    容器：{", ".join(ms.get("container", []))}<br>
    サンプル：{", ".join(ms.get("sample", []))}<br>
    灯油：{", ".join(ms.get("oil", []))}
    </div>
    """,
    unsafe_allow_html=True
)

# =================================================
# サイドバー
# =================================================
members = ["菅原","阿部","澤","畠山","猿田","谷川","村手","武藤","小笠原","藤田"]

st.sidebar.header("操作・月次設定")

# --- テンプレ ---
templates = {
    "外船":"外船","チーム会議":"チーム会議",
    "安全衛生委員会":"安全衛生委員会"
}
temp = st.sidebar.selectbox("予定テンプレ", [""]+list(templates))
day_sel = st.sidebar.number_input("日付", 1, days, 1)

if st.sidebar.button("テンプレ入力"):
    d = str(day_sel)
    st.session_state.data["schedule"][d] = templates[temp]
    st.session_state.pop(f"sch_{day_sel}", None)
    st.rerun()

# --- 当番自動 ---
start = st.sidebar.selectbox("開始当番（1日）", members)
if st.sidebar.button("当番自動割当（土日祝除外）"):
    idx = members.index(start)
    for d in range(1, days+1):
        date = datetime.date(year, month, d)
        if date.weekday()>=5 or jpholiday.is_holiday(date):
            continue
        st.session_state.data["duty"][str(d)] = members[idx%len(members)]
        st.session_state.pop(f"duty_{d}", None)
        idx+=1
    st.rerun()

# --- 月次設定 ---
st.sidebar.markdown("---")
ms["start"] = st.sidebar.selectbox("開始当番メンバー", members, key="ms_start")
ms["container"] = st.sidebar.multiselect("容器", members, max_selections=3, key="ms_c")
ms["sample"] = st.sidebar.multiselect("サンプル", members, max_selections=3, key="ms_s")
ms["oil"] = st.sidebar.multiselect("灯油", members, max_selections=3, key="ms_o")

# =================================================
# CSV入出力（★今回の要件）
# =================================================
st.sidebar.markdown("---")
st.sidebar.markdown("### CSV")

# ダウンロード
df = pd.DataFrame({
    "日": list(range(1, days+1)),
    "当番": [st.session_state.data["duty"][str(d)] for d in range(1, days+1)],
    "予定": [st.session_state.data["schedule"][str(d)] for d in range(1, days+1)],
})
st.sidebar.download_button(
    "CSV保存",
    df.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"schedule_{year}_{month}.csv"
)

# アップロード
up = st.sidebar.file_uploader("CSV読込", type="csv")
if up:
    df = pd.read_csv(up)
    for _, r in df.iterrows():
        d = str(int(r["日"]))
        st.session_state.data["duty"][d] = "" if pd.isna(r["当番"]) else r["当番"]
        st.session_state.data["schedule"][d] = "" if pd.isna(r["予定"]) else r["予定"]
        st.session_state.pop(f"duty_{d}", None)
        st.session_state.pop(f"sch_{d}", None)
    st.rerun()

# =================================================
# 日付表（スクロール）
# =================================================
def style(d):
    date = datetime.date(year, month, d)
    if jpholiday.is_holiday(date): return "#ffe5e5","red"
    if date.weekday()==5: return "#e8f0ff","blue"
    if date.weekday()==6: return "#ffe5e5","red"
    return "white","black"

st.markdown("<div class='scroll-area'>", unsafe_allow_html=True)
colL,colR = st.columns(2)

def draw(d):
    bg,c = style(d)
    k=str(d)
    a,b,c3 = st.columns([1,2,7])
    with a:
        st.markdown(f"<div style='background:{bg};color:{c}'>{d}</div>",unsafe_allow_html=True)
    with b:
        st.session_state.data["duty"][k]=st.text_input("",st.session_state.data["duty"][k],key=f"duty_{d}",label_visibility="collapsed")
    with c3:
        st.session_state.data["schedule"][k]=st.text_input("",st.session_state.data["schedule"][k],key=f"sch_{d}",label_visibility="collapsed")

with colL:
    for d in range(1,min(16,days+1)): draw(d)
with colR:
    for d in range(16,days+1): draw(d)

st.markdown("</div>", unsafe_allow_html=True)

# =================================================
# 自動保存
# =================================================
with open(data_file,"w",encoding="utf-8") as f:
    json.dump(st.session_state.data,f,ensure_ascii=False,indent=2)
