import streamlit as st
import pandas as pd
import requests
import fitz  # PyMuPDF 轉圖神器
import streamlit.components.v1 as components # 💡 氣泡對話框無敵防護罩

# ==========================================
# 1. 頁面與基礎設定
# ==========================================
st.set_page_config(page_title="國中自然60天逆襲", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
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
# 3. 本地 PDF 光速讀取
# ==========================================
@st.cache_data(ttl=3600)
def get_pdf_page_image(local_pdf_path, page_index):
    try:
        doc = fitz.open(local_pdf_path)
        if page_index >= doc.page_count:
            doc.close()
            return "PAGE_OUT_OF_RANGE"
            
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0)) 
        img_data = pix.tobytes("png")
        doc.close()
        return img_data
    except Exception as e:
        return str(e)

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

    # --- 聽覺區 ---
    st.subheader("🔊 聽講區 (1.75x 衝刺音頻)")
    audio_path = str(row['Audio_Path']).strip()
    if audio_path.startswith('/'): audio_path = audio_path[1:]
    audio_url = f"{GITHUB_RAW}{audio_path}"
    st.audio(audio_url)

    # --- 視覺區 ---
    st.divider()
    st.subheader("📝 彥君老師手繪講義")
    
    target_page = st.number_input("翻閱講義頁碼：", min_value=1, value=1)
    local_pdf_path = "notes.pdf" 
    
    with st.spinner("⏳ 光速載入講義圖檔中..."):
        result = get_pdf_page_image(local_pdf_path, target_page - 1)
        
        if result == "PAGE_OUT_OF_RANGE":
            st.warning(f"⚠️ 彥君老師提醒：這份講義沒有第 {target_page} 頁喔！請把頁碼調小。")
        elif isinstance(result, bytes): 
            st.image(result, use_container_width=True, caption=f"講義第 {target_page} 頁")
        else:
            st.error(f"⚠️ 讀取失敗。系統回報：{result}")

    # --- 💡 終極無敵氣泡對話框 ---
    st.divider()
    st.subheader("💬 衝刺劇本 (對話字幕)")
    
    script_path = str(row['Script_Path']).strip()
    if script_path.startswith('/'): script_path = script_path[1:]
    script_url = f"{GITHUB_RAW}{script_path}"
    
    try:
        res = requests.get(script_url)
        res.encoding = 'utf-8'
        lines = res.text.split('\n')
        
        # 使用原生 HTML/CSS 寫法，保證不會被破壞
        chat_html = """
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body { font-family: 'PingFang TC', sans-serif; background-color: #f4f6f9; padding: 15px; margin: 0; }
            .chat-container { display: flex; flex-direction: column; gap: 15px; }
            .bubble-left { align-self: flex-start; background-color: #e3f2fd; padding: 12px 18px; border-radius: 15px 15px 15px 0; max-width: 85%; box-shadow: 1px 1px 3px rgba(0,0,0,0.1); color: #000; line-height: 1.6; }
            .bubble-right { align-self: flex-end; background-color: #ffe0b2; padding: 12px 18px; border-radius: 15px 15px 0 15px; max-width: 85%; box-shadow: 1px 1px 3px rgba(0,0,0,0.1); color: #000; line-height: 1.6; }
            .system-msg { text-align: center; color: #888; font-size: 0.9em; margin: 10px 0; }
            .name-tag { font-weight: bold; margin-bottom: 5px; font-size: 0.9em; color: #555;}
        </style>
        </head>
        <body>
        <div class="chat-container">
        """
        
        current_speaker = None
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # 支援「同一行」寫法 (彥君老師：內容)
            if "：" in line and len(line.split("：", 1)[0]) < 10:
                speaker, content = line.split("：", 1)
                if "彥君老師" in speaker:
                    chat_html += f'<div class="bubble-left"><div class="name-tag">👨‍🏫 彥君老師</div>{content}</div>'
                elif "曉臻助教" in speaker:
                    chat_html += f'<div class="bubble-right"><div class="name-tag">👩‍🔬 曉臻助教</div>{content}</div>'
                else:
                    chat_html += f'<div class="system-msg">{line}</div>'
            # 支援「上下換行」寫法 (你的截圖寫法)
            else:
                if "彥君老師" in line and len(line) < 15:
                    current_speaker = "彥君老師"
                elif "曉臻助教" in line and len(line) < 15:
                    current_speaker = "曉臻助教"
                elif line.startswith("【") or line.startswith("<") or "字數" in line or "目標" in line or "角色" in line:
                    chat_html += f'<div class="system-msg">{line}</div>'
                else:
                    if current_speaker == "彥君老師":
                        chat_html += f'<div class="bubble-left"><div class="name-tag">👨‍🏫 彥君老師</div>{line}</div>'
                        current_speaker = None # 講完一句重置
                    elif current_speaker == "曉臻助教":
                        chat_html += f'<div class="bubble-right"><div class="name-tag">👩‍🔬 曉臻助教</div>{line}</div>'
                        current_speaker = None
                    else:
                        chat_html += f'<div class="system-msg">{line}</div>'
                        
        chat_html += "</div></body></html>"
        
        # 🛡️ 開啟無敵防護罩，獨立網頁渲染！
        components.html(chat_html, height=450, scrolling=True)
            
    except Exception as e:
        st.error(f"劇本載入失敗。請檢查 {script_url} 是否存在。")
else:
    st.error("資料庫連線中...請稍後再試。")
