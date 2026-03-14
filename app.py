import streamlit as st
import pandas as pd
import requests
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
# 3. 終極光速版：直接讀取本地 PDF (免網路下載)
# ==========================================
@st.cache_data(ttl=3600)
def get_pdf_page_image(local_pdf_path, page_index):
    try:
        # 檔案就在旁邊，直接打開就好！不需要去網路下載
        doc = fitz.open(local_pdf_path)
        
        # 防呆：檢查頁數
        if page_index >= doc.page_count:
            doc.close()
            return "PAGE_OUT_OF_RANGE"
            
        # 轉換高畫質圖片
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0)) 
        img_data = pix.tobytes("png")
        doc.close()
        return img_data
    except Exception as e:
        return str(e) # 顯示真實錯誤原因

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
    
    target_page = st.number_input("翻閱講義頁碼：", min_value=1, value=1)
    
    # 直接指定檔名，不使用網址
    local_pdf_path = "notes.pdf" 
    
    with st.spinner("⏳ 光速載入講義圖檔中..."):
        result = get_pdf_page_image(local_pdf_path, target_page - 1)
        
        if result == "PAGE_OUT_OF_RANGE":
            st.warning(f"⚠️ 彥君老師提醒：這份講義沒有第 {target_page} 頁喔！請把頁碼調小。")
        elif isinstance(result, bytes): 
            st.image(result, use_container_width=True, caption=f"講義第 {target_page} 頁")
        else:
            st.error(f"⚠️ 讀取失敗。系統回報：{result}")

   # --- 文字區：Spotify 劇本字幕模式 ---
    st.divider()
    st.subheader("💬 衝刺劇本 (對話字幕)")
    
    script_path = str(row['Script_Path']).strip()
    if script_path.startswith('/'): script_path = script_path[1:]
    script_url = f"{GITHUB_RAW}{script_path}"
    
    try:
        res = requests.get(script_url)
        res.encoding = 'utf-8'
        lines = res.text.split('\n')
        
        # 建立一個有高度限制、可手動滾動的字幕視窗
        chat_html = '<div style="height: 400px; overflow-y: auto; padding: 15px; background-color: #f4f6f9; border-radius: 10px; border: 1px solid #ddd;">'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 💡 關鍵修正：HTML 標籤全部寫在同一行，絕對不准縮排！
            if "彥君老師：" in line:
                content = line.replace("彥君老師：", "").strip()
                chat_html += f'<div style="margin-bottom: 15px; text-align: left;"><span style="background-color: #e3f2fd; padding: 10px 15px; border-radius: 15px; display: inline-block; max-width: 85%; color: #000; box-shadow: 1px 1px 3px rgba(0,0,0,0.1);"><b>👨‍🏫 彥君老師</b><br>{content}</span></div>'
            elif "曉臻助教：" in line:
                content = line.replace("曉臻助教：", "").strip()
                chat_html += f'<div style="margin-bottom: 15px; text-align: right;"><span style="background-color: #ffe0b2; padding: 10px 15px; border-radius: 15px; display: inline-block; max-width: 85%; text-align: left; color: #000; box-shadow: 1px 1px 3px rgba(0,0,0,0.1);"><b>👩‍🔬 曉臻助教</b><br>{content}</span></div>'
            else:
                # 其他旁白或標題
                chat_html += f'<div style="text-align: center; color: #888; font-size: 0.9em; margin: 10px 0;">{line}</div>'
                
        chat_html += '</div>'
        
        # 顯示對話框
        st.markdown(chat_html, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"劇本載入失敗。請檢查 {script_url} 是否存在。")
else:
    st.error("資料庫連線中...請稍後再試。")
