import streamlit as st
import pandas as pd
import requests
import time
import fitz  # PyMuPDF 轉圖神器

# ==========================================
# 1. 頁面與基礎設定
# ==========================================
st.set_page_config(page_title="國中自然60天逆襲", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    .typing-text { 
        font-family: 'PingFang TC', sans-serif; line-height: 1.8; color: #2c3e50; 
        background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #eee;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 資料庫與路徑設定
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
# 3. 抄回你的絕招：PDF 轉圖片顯示 (保證不破圖)
# ==========================================
@st.cache_data(ttl=3600)
def get_pdf_page_image(pdf_url, page_index):
    try:
        # 1. 把 PDF 從 GitHub 下載到暫存檔
        response = requests.get(pdf_url)
        response.raise_for_status()
        with open("temp_notes.pdf", "wb") as f:
            f.write(response.content)
        
        # 2. 使用 fitz 轉成清晰的圖片 (矩陣放大切換高畫質)
        doc = fitz.open("temp_notes.pdf")
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0)) 
        img_data = pix.tobytes("png")
        doc.close()
        return img_data
    except Exception as e:
        return None

# ==========================================
# 4. 學生前台主介面
# ==========================================
st.title("🎧 自然科學真理 PODCAST")
st.caption("免登入、免 API，直接開啟衝刺模式！")

df = load_data()

if df is not None:
    # 導航選單
    unit_list = df['Day'].tolist()
    selected = st.selectbox("📅 選擇今日進度：", unit_list)
    row = df[df['Day'] == selected].iloc[0]

    st.divider()
    st.header(f"📍 {row['Title']}")

    # --- 聽覺區：播放預錄好的 MP3 ---
    st.subheader("🔊 聽講區 (1.75x 衝刺音頻)")
    audio_path = str(row['Audio_Path']).strip()
    if audio_path.startswith('/'): audio_path = audio_path[1:]
    audio_url = f"{GITHUB_RAW}{audio_path}"
    st.audio(audio_url)

    # --- 視覺區：PDF 轉圖片顯示 ---
    st.divider()
    st.subheader("📝 彥君老師手繪講義")
    
    # 讓學生選擇要看講義的第幾頁 (預設為第 1 頁)
    target_page = st.number_input("翻閱講義頁碼：", min_value=1, value=1)
    pdf_raw_url = f"{GITHUB_RAW}notes.pdf"
    
    with st.spinner("⏳ 載入講義圖檔中..."):
        # 注意：fitz 的 page_index 是從 0 開始算，所以 target_page 要減 1
        page_img = get_pdf_page_image(pdf_raw_url, target_page - 1)
        
        if page_img:
            st.image(page_img, use_container_width=True, caption=f"講義第 {target_page} 頁")
        else:
            st.error("⚠️ 圖檔轉換失敗，請確認 notes.pdf 是否存在於 GitHub 根目錄。")

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
                time.sleep(0.005)
        except:
            st.error("逐字稿載入失敗。")

else:
    st.error("資料庫連線中...請稍後再試。")
