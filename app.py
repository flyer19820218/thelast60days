import streamlit as st
import pandas as pd
import requests
import time

# --- 1. 頁面設定 ---
st.set_page_config(page_title="考前60天衝刺", layout="centered")

# --- 2. 路徑設定 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
GITHUB_RAW = "https://raw.githubusercontent.com/flyer19820218/thelast60days/main/"
GEMINI_API_KEY = "AIzaSyCrcKESi4rF0_VSdV3Bsica_dem612c3F4"

@st.cache_data(ttl=60)
def load_data():
    return pd.read_csv(SHEET_URL)

# --- 3. 介面呈現 ---
st.title("🎧 自然科學真理 PODCAST")
df = load_data()

if df is not None:
    unit_list = df['Day'].tolist()
    selected = st.selectbox("📅 選擇今日進度：", unit_list)
    row = df[df['Day'] == selected].iloc[0]

    st.divider()
    st.header(f"📍 {row['Title']}")

    # 圖片顯示
    with st.expander("💡 AI 複習圖卡描述"):
        st.write(row['Image_Prompt'])
    
    # 這裡顯示一張示意圖
    st.image("https://via.placeholder.com/600x400.png?text=AI+Learning+Card", caption="示意圖 (繪圖功能載入中)")

    # 播放器
    st.subheader("🔊 聽講區")
    audio_url = f"{GITHUB_RAW}{row['Audio_Path']}"
    st.audio(audio_url)

    # 文字稿
    if st.button(f"📖 閱讀 {selected} 講義"):
        script_url = f"{GITHUB_RAW}{row['Script_Path']}"
        res = requests.get(script_url)
        res.encoding = 'utf-8'
        
        # 打字機效果
        placeholder = st.empty()
        full_t = ""
        for c in res.text:
            full_t += c
            placeholder.markdown(f"```text\n{full_t}\n```")
            time.sleep(0.01)

else:
    st.error("無法載入資料庫，請檢查 Google Sheet 權限。")
