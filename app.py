import streamlit as st
import pandas as pd
import requests
import base64
import time

# ==========================================
# 1. 頁面與基礎設定
# ==========================================
st.set_page_config(page_title="國中自然60天逆襲", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    .podcast-card {
        background-color: #ffffff; padding: 15px; border-radius: 15px;
        border-left: 5px solid #4CAF50; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .typing-text { 
        font-family: 'PingFang TC', sans-serif; line-height: 1.8; color: #2c3e50; 
        background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #eee;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 資料庫與路徑設定 (替換為你的帳號)
# ==========================================
USER = "flyer19820218"
REPO = "thelast60days"
GITHUB_RAW = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/"

@st.cache_data(ttl=60)
def load_data():
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
    try:
        return pd.read_csv(SHEET_URL)
    except Exception as e:
        return None

# ==========================================
# 3. PDF 終極內嵌顯示器 (防破圖)
# ==========================================
@st.cache_data(ttl=3600) # 快取 PDF，避免學生每次切換都要重新下載
def get_pdf_display(pdf_url):
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()
        base64_pdf = base64.b64encode(response.content).decode('utf-8')
        return f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf" style="border:none; border-radius:10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"></iframe>'
    except:
        return "<p style='color:red;'>⚠️ PDF 講義載入失敗，請確認 GitHub 檔案路徑。</p>"

# ==========================================
# 4. 學生前台主介面
# ==========================================
st.title("🎧 自然科學真理 PODCAST")
st.caption("彥君老師 & 曉臻助教：免登入、免 API，直接開啟衝刺模式！")

df = load_data()

if df is not None:
    # 導航選單
    unit_list = df['Day'].tolist()
    selected = st.selectbox("📅 選擇今日進度：", unit_list)
    row = df[df['Day'] == selected].iloc[0]

    st.divider()
    st.header(f"📍 {row['Title']}")

    # --- 聽覺區：播放預錄好的 MP3 ---
    st.markdown('<div class="podcast-card"><b>🔊 點擊播放 (1.75x 衝刺音頻)</b></div>', unsafe_allow_html=True)
    audio_path = str(row['Audio_Path']).strip()
    if audio_path.startswith('/'): audio_path = audio_path[1:]
    audio_url = f"{GITHUB_RAW}{audio_path}"
    st.audio(audio_url)

    # --- 視覺區：顯示 PDF 講義 ---
    st.divider()
    st.subheader("📝 彥君老師手繪講義")
    pdf_raw_url = f"{GITHUB_RAW}notes.pdf"
    
    # 全螢幕下載按鈕 (給手機瀏覽器備用)
    st.link_button("📂 若畫面太小，點此全螢幕打開 PDF", pdf_raw_url)
    
    # 直接在畫面中顯示 PDF
    st.markdown(get_pdf_display(pdf_raw_url), unsafe_allow_html=True)

    # --- 文字區：逐字稿打字機 ---
    st.divider()
    if st.button(f"📖 展開本集逐字稿"):
        script_path = str(row['Script_Path']).strip()
        if script_path.startswith('/'): script_path = script_path[1:]
        script_url = f"{GITHUB_RAW}{script_path}"
        
        try:
            res = requests.get(script_url)
            res.encoding = 'utf-8'
            
            placeholder = st.empty()
            typed_text = ""
            for char in res.text:
                typed_text += char
                placeholder.markdown(f'<div class="typing-text">{typed_text}</div>', unsafe_allow_html=True)
                time.sleep(0.005) # 極速打字機
        except:
            st.error("逐字稿載入失敗。")

else:
    st.error("資料庫連線中...請稍後再試。")
