import streamlit as st
import pandas as pd
import requests
import time

# --- 1. 頁面設定 (手機優先排版) ---
st.set_page_config(page_title="自然科學的真理", layout="centered")

# 自定義 CSS 美化
st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    .stAudio { width: 100%; }
    .typing-text { 
        font-family: 'Courier New', Courier, monospace; 
        line-height: 1.8; 
        color: #2c3e50; 
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #eee;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據庫與路徑設定 ---
# 你的 Google Sheet CSV 直連連結
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"

# 你的 GitHub 基礎路徑 (結尾務必有斜槓)
GITHUB_RAW = "https://raw.githubusercontent.com/你的GitHub帳號/thelast60days/main/"

@st.cache_data(ttl=300) # 每 5 分鐘快取更新一次
def load_data():
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        return df
    except Exception as e:
        st.error(f"數據庫讀取失敗: {e}")
        return None

# --- 3. 側邊欄與標題 ---
st.title("🎧 自然科學真理 PODCAST")
st.caption("會考 60 天衝刺 - 彥君老師 & 曉臻助教")

df = load_data()

if df is not None:
    # 選擇單元 (對應 Google Sheet 的 Day 欄位)
    unit_options = df['Day'].tolist()
    selected_unit = st.selectbox("📅 選擇今日衝刺進度：", unit_options)
    
    # 取得選中單元的整行資料
    row = df[df['Day'] == selected_unit].iloc[0]
    
    st.divider()
    
    # --- 4. 內容顯示區 ---
    st.subheader(f"📍 {row['Title']}")
    
    # AI 提示詞區域 (可視化參考)
    with st.expander("💡 本集 AI 核心圖解概念"):
        st.write(row['Image_Prompt'])
    
    # --- 5. Podcast 播放器 ---
    audio_full_url = f"{GITHUB_RAW}{row['Audio_Path']}"
    st.audio(audio_full_url)
    st.info("點擊上方播放鍵開始聽講")

    # --- 6. 打字機文字稿 ---
    st.divider()
    st.write("📝 **逐字衝刺講義**")
    
    if st.button(f"🚀 開始/重新閱讀 {selected_unit} 文字稿"):
        script_url = f"{GITHUB_RAW}{row['Script_Path']}"
        try:
            response = requests.get(script_url)
            response.encoding = 'utf-8' # 強制編碼避免亂碼
            full_text = response.text
            
            # 使用 Streamlit 內建 write_stream 達成打字機效果
            def stream_data():
                for word in full_text:
                    yield word
                    time.sleep(0.01) # 調整打字速度
            
            st.write_stream(stream_data)
            
        except Exception as e:
            st.error(f"無法讀取文字稿：{e}")
            st.warning("請確認 GitHub Repository 是否設為 Public (公開)，且路徑正確。")

else:
    st.warning("請檢查 Google Sheet 連結與權限。")

# --- 7. 腳註 ---
st.divider()
st.caption("💪 彥君老師提醒：聽完記得站起來動一動，活化你的大腦多巴胺！")
