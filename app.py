import streamlit as st
import pandas as pd
import requests
import base64

# --- 1. 頁面設定 ---
st.set_page_config(page_title="國中自然60天逆襲", layout="centered")

# --- 2. 路徑設定 (替換你的帳號) ---
USER = "flyer19820218"
REPO = "thelast60days"
GITHUB_RAW = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/"
# 使用 jsDelivr 服務來穩定顯示 PDF
PDF_URL = f"https://cdn.jsdelivr.net/gh/{USER}/{REPO}/notes.pdf"

@st.cache_data(ttl=60)
def load_data():
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
    return pd.read_csv(SHEET_URL)

# --- 3. PDF 顯示組件 ---
def display_pdf(url):
    # 用 iframe 嵌入，這是手機最友好的顯示方式
    pdf_display = f'<iframe src="{url}" width="100%" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- 4. 主程式 ---
st.title("🎧 自然科學真理 PODCAST")
st.caption("彥君老師 & 曉臻助教：考前 60 天陪你衝 A")

df = load_data()

if df is not None:
    unit_list = df['Day'].tolist()
    selected = st.selectbox("📅 選擇今日進度：", unit_list)
    row = df[df['Day'] == selected].iloc[0]

    st.divider()
    
    # 語音區
    st.subheader(f"🔊 {row['Title']}")
    audio_url = f"{GITHUB_RAW}{row['Audio_Path']}"
    st.audio(audio_url)
    st.caption("⚡️ 建議使用 1.75x 聽講更高效")

    # PDF 區
    st.divider()
    st.subheader("📝 彥君老師手繪講義")
    st.link_button("📂 全螢幕打開 PDF 講義", PDF_URL)
    display_pdf(PDF_URL)

    # 逐字稿區 (選用)
    with st.expander("📖 查看本集逐字稿"):
        script_url = f"{GITHUB_RAW}{row['Script_Path']}"
        res = requests.get(script_url)
        res.encoding = 'utf-8'
        st.write(res.text)

else:
    st.error("資料庫連線中...")
