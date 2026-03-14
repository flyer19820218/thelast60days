import streamlit as st
import pandas as pd
import requests
import time

# --- 1. 設定 ---
st.set_page_config(page_title="國中自然60天逆襲", layout="centered")

# --- 2. 路徑與資料 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
GITHUB_RAW = "https://raw.githubusercontent.com/flyer19820218/thelast60days/main/"

@st.cache_data(ttl=60)
def load_data():
    return pd.read_csv(SHEET_URL)

# --- 3. 主介面 ---
st.title("🎧 自然科學真理 PODCAST")
df = load_data()

if df is not None:
    unit_list = df['Day'].tolist()
    selected = st.selectbox("📅 選擇今日衝刺進度：", unit_list)
    row = df[df['Day'] == selected].iloc[0]

    st.divider()
    st.header(f"📍 {row['Title']}")

    # --- 4. 顯示你的手繪圖解 (從 GitHub 讀取) ---
    st.subheader("🎨 彥君老師手繪講義")
    
    # 這裡我們假設你在 GitHub 建立了 images/ 資料夾，檔名對應 p1.png, p2.png
    # 或者是直接放 PDF 連結
    img_filename = row['Script_Path'].replace('scripts/', 'images/').replace('.txt', '.png')
    img_url = f"{GITHUB_RAW}{img_filename}"
    
    # 嘗試顯示圖片，如果沒有圖片則顯示 Prompt 文字
    try:
        st.image(img_url, caption=f"本日重點圖解：{row['Title']}", use_container_width=True)
    except:
        st.info(f"💡 本集核心概念：{row['Image_Prompt']}")
        st.caption("（手繪圖檔載入中，請確保 GitHub images/ 資料夾已有對應 PNG）")

    # --- 5. 語音播放器 ---
    st.markdown("---")
    audio_url = f"{GITHUB_RAW}{row['Audio_Path']}"
    st.audio(audio_url)
    st.caption("🔊 建議開啟 1.75x 語速衝刺")

    # --- 6. 文字稿 ---
    if st.button(f"📖 展開文字講義"):
        script_url = f"{GITHUB_RAW}{row['Script_Path']}"
        res = requests.get(script_url)
        res.encoding = 'utf-8'
        st.markdown(f'<div style="background-color:white; padding:15px; border-radius:10px; border:1px solid #ddd;">{res.text}</div>', unsafe_allow_html=True)
