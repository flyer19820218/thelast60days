import streamlit as st
import pandas as pd
import requests
import time
import base64

# ==========================================
# 區塊 1：基礎設定與 CSS 美化
# 功能：定義手機版排版、播放器樣式
# ==========================================
st.set_page_config(page_title="國中自然60天逆襲", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    .stAudio { width: 100%; margin-top: 10px; }
    .typing-text { 
        font-family: 'PingFang TC', 'Microsoft JhengHei', sans-serif; 
        line-height: 1.8; color: #2c3e50; background-color: #ffffff;
        padding: 20px; border-radius: 10px; border: 1px solid #eee;
    }
    .podcast-card {
        background-color: #ffffff; padding: 15px; border-radius: 15px;
        border-left: 5px solid #4CAF50; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 區塊 2：數據路徑與 API 設定
# ==========================================
# 你的 Google Sheet CSV 直連連結
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"

# 你的 GitHub 基礎路徑 (結尾務必有斜槓)
GITHUB_RAW = "https://raw.githubusercontent.com/flyer19820218/thelast60days/main/"

# --- 🔑 你的 API KEY (已填入) ---
GEMINI_API_KEY = "AIzaSyCrcKESi4rF0_VSdV3Bsica_dem612c3F4"

@st.cache_data(ttl=60) # 衝刺期設定 1 分鐘更新一次
def load_data():
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        return df
    except Exception as e:
        st.error(f"數據庫讀取失敗: {e}")
        return None

# ==========================================
# 核心功能：AI 圖像生成 (方案 B)
# 功能：調用 Gemini 3 Flash Image 真正繪圖
# ==========================================
def generate_ai_image(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-image:generateImages?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    # 增加科學繪圖的關鍵字，讓圖片更專業、清晰
    refined_prompt = f"Educational scientific illustration, clear diagram, labeled parts, white background, flat design style: {prompt}"
    
    data = {
        "instances": [{"prompt": refined_prompt}],
        "parameters": {"sampleCount": 1}
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            # 取得 Base64 圖片並轉換
            img_b64 = response.json()['predictions'][0]['bytesBase64Encoded']
            return f"data:image/png;base64,{img_b64}"
        else:
            st.error(f"繪圖 API 報錯: {response.text}")
            return None
    except Exception as e:
        st.error(f"繪圖連線失敗: {e}")
        return None

# ==========================================
# 區塊 3：導航選單 (考前 60 天進度)
# ==========================================
st.title("🎧 自然科學真理 PODCAST")
st.caption("國中自然會考 60 天衝刺 - 彥君老師 & 曉臻助教")

df = load_data()

if df is not None:
    # 選擇單元
    unit_options = df['Day'].tolist()
    selected_unit = st.selectbox("📅 選擇今日衝刺進度：", unit_options)
    
    # 取得資料
    row = df[df['Day'] == selected_unit].iloc[0]
    
    st.divider()
    st.subheader(f"📍 當日進度：{row['Title']}")

    # ==========================================
    # 區塊 4：AI 複習圖卡顯示區 (圖來了！)
    # ==========================================
    with st.expander("💡 查看 AI 複習圖卡描述"):
        st.write(row['Image_Prompt'])
    
    # 使用 st.spinner 轉圈圈，避免網頁卡住
    with st.spinner(f"⏳ 彥君老師正在調用 AI 生成「{row['Title']}」的核心圖卡..."):
        # 真正呼叫 API 繪圖
        img_result = generate_ai_image(row['Image_Prompt'])
        
        if img_result:
            st.image(img_result, caption=f"彥君老師提供的 AI 示意圖：{row['Image_Prompt']}", use_container_width=True)
        else:
            st.warning("⚠️ 圖片生成失敗，請檢查 API Key 或 Prompt。")

    # ==========================================
    # 區塊 5：Podcast 語音播放區
    # ==========================================
    st.divider()
    st.markdown('<div class="podcast-card"><b>🎙️ 點擊播放衝刺音頻 (1.75x 高效模式)</b></div>', unsafe_allow_html=True)
    
    # 確保路徑拼接正確
    audio_path = str(row['Audio_Path']).strip()
    if audio_path.startswith('/'):
        audio_path = audio_path[1:]
    
    audio_full_url = f"{GITHUB_RAW}{audio_path}"
    st.audio(audio_full_url)

    # ==========================================
    # 區塊 6：打字機文字稿區
    # ==========================================
    st.divider()
    if st.button(f"🚀 展開 {selected_unit} 衝刺文字講義"):
        script_path = str(row['Script_Path']).strip()
        if script_path.startswith('/'):
            script_path = script_path[1:]
            
        script_url = f"{GITHUB_RAW}{script_path}"
        try:
            response = requests.get(script_url)
            response.encoding = 'utf-8' 
            full_text = response.text
            
            placeholder = st.empty()
            typed_text = ""
            # 模擬打字機效果
            for char in full_text:
                typed_text += char
                placeholder.markdown(f'<div class="typing-text">{typed_text}</div>', unsafe_allow_html=True)
                time.sleep(0.01)
            
        except:
            st.error("講義讀取失敗")

else:
    st.warning("請先完成 Google Sheet 設定。")
