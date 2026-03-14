import streamlit as st
import pandas as pd
import requests
import time

# --- 1. 頁面設定 (手機優先排版) ---
st.set_page_config(page_title="考前60天衝刺", layout="centered")

# 自定義 CSS 美化
st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    .stAudio { width: 100%; }
    .typing-text { 
        font-family: 'PingFang TC', 'Microsoft JhengHei', sans-serif; 
        line-height: 1.8; 
        color: #2c3e50; 
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #eee;
    }
    .podcast-card {
        background-color: #ffffff; padding: 15px; border-radius: 15px;
        border-left: 5px solid #4CAF50; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據庫與路徑設定 ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"

# ⚠️ 請記得修改下方為你的 GitHub 帳號 ⚠️
GITHUB_RAW = "https://raw.githubusercontent.com/你的GitHub帳號/thelast60days/main/"

# 🔑 API KEY
GEMINI_API_KEY = "AIzaSyCrcKESi4rF0_VSdV3Bsica_dem612c3F4"

@st.cache_data(ttl=60) # 衝刺期設定 1 分鐘更新一次
def load_data():
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        return df
    except Exception as e:
        st.error(f"數據庫讀取失敗: {e}")
        return None

# --- AI 繪圖函數 ---
def generate_nature_image(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-image:generateImages?key={GEMINI_API_KEY}"
    payload = {
        "instances": [{"prompt": f"Professional scientific illustration, white background: {prompt}"}]
    }
    try:
        # 這裡目前回傳佔位圖，串接正式 API 後可替換為真實 Base64 轉換邏輯
        return f"https://via.placeholder.com/600x400.png?text={prompt}"
    except:
        return None

# --- 3. 標題與選單 ---
st.title("🎧 自然科學真理 PODCAST")
st.caption("會考 60 天衝刺 - 彥君老師 & 曉臻助教")

df = load_data()

if df is not None:
    # 選擇單元
    unit_options = df['Day'].tolist()
    selected_unit = st.selectbox("📅 選擇今日衝刺進度：", unit_options)
    
    # 取得資料
    row = df[df['Day'] == selected_unit].iloc[0]
    
    st.divider()
    st.subheader(f"📍 {row['Title']}")
    
    # --- 4. AI 內容顯示區 ---
    with st.expander("💡 本集 AI 核心圖解概念"):
        st.write(row['Image_Prompt'])
    
    # 顯示 AI 生成圖片
    img_result = generate_nature_image(row['Image_Prompt'])
    if img_result:
        st.image(img_result, caption="彥君老師的重點示意圖")

    # --- 5. Podcast 語音播放 ---
    st.markdown('<div class="podcast-card"><b>🎙️ 點擊播放衝刺音頻</b></div>', unsafe_allow_html=True)
    
    audio_path = str(row['Audio_Path']).strip()
    if audio_path.startswith('/'):
        audio_path = audio_path[1:]
    
    audio_full_url = f"{GITHUB_RAW}{audio_path}"
    st.audio(audio_full_url)

    # --- 6. 打字機文字稿 ---
    st.divider()
    st.write("📝 **逐字衝刺講義**")
    
    if st.button(f"🚀 開始/重新閱讀 {selected_unit} 文字稿"):
        script_url = f"{GITHUB_RAW}{row['Script_Path']}"
        try:
            response = requests.get(script_url)
            response.encoding = 'utf-8'
            full_text = response.text
            
            placeholder = st.empty()
            typed_text = ""
            for char in full_text:
                typed_text += char
                placeholder.markdown(f'<div class="typing-text">{typed_text}</div>', unsafe_allow_html=True)
                time.sleep(0.01)
                
        except Exception as e:
            st.error(f"無法讀取文字稿：{e}")

    # --- 7. 腳註 ---
    st.divider()
    st.caption("💪 彥君老師提醒：聽完記得站起來動一動，活化你的大腦多巴胺！")

else:
    st.warning("請檢查 Google Sheet 連結與權限。")
