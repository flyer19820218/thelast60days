import streamlit as st
import pandas as pd
import requests
import fitz  # PyMuPDF 轉圖神器

# ==========================================
# 1. 頁面與基礎設定 (維持漂亮的字體)
# ==========================================
st.set_page_config(page_title="國中自然60天逆襲", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    /* 強制全局字體 */
    html, body, [class*="css"], p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
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

    # --- 💡 原生超穩定對話框 ---
    st.divider()
    st.subheader("💬 衝刺劇本 (對話字幕)")
    
    script_path = str(row['Script_Path']).strip()
    if script_path.startswith('/'): script_path = script_path[1:]
    script_url = f"{GITHUB_RAW}{script_path}"
    
    try:
        res = requests.get(script_url)
        res.encoding = 'utf-8'
        lines = res.text.split('\n')
        
        # 1. 解析腳本
        chat_data = []
        current_speaker = "system"
        buffer = []
        
        def flush_buffer():
            if buffer:
                # 把陣列裡的字串組合起來，用 Markdown 的換行格式
                chat_data.append({"role": current_speaker, "content": "  \n".join(buffer)})
                buffer.clear()
                
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # 略過單純介紹角色的那行
            if "角色" in line and "彥君" in line:
                buffer.append(line)
                continue

            # 抓取說話者 (相容你有加 Emoji 的寫法)
            if "彥君" in line and len(line) <= 20 and "：" not in line:
                flush_buffer()
                current_speaker = "彥君"
            elif "曉臻" in line and len(line) <= 20 and "：" not in line:
                flush_buffer()
                current_speaker = "曉臻"
            elif "：" in line and ("彥君" in line.split("：")[0] or "曉臻" in line.split("：")[0]):
                flush_buffer()
                speaker, content = line.split("：", 1)
                current_speaker = "彥君" if "彥君" in speaker else "曉臻"
                buffer.append(content)
                flush_buffer()
                current_speaker = "system"
            else:
                buffer.append(line)
        flush_buffer()
        
        # 2. 原生渲染 (保證出現，而且自帶滾動條)
        with st.container(height=500):
            for msg in chat_data:
                if msg["role"] == "彥君":
                    with st.chat_message("user", avatar="👨‍🏫"):
                        st.markdown(f"**彥君老師** \n{msg['content']}")
                elif msg["role"] == "曉臻":
                    with st.chat_message("assistant", avatar="👩‍🔬"):
                        st.markdown(f"**曉臻助教** \n{msg['content']}")
                else:
                    st.markdown(f"<div style='text-align:center; color:#888; font-size:0.9em; margin:10px 0;'>{msg['content']}</div>", unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"劇本載入失敗。系統回報：{e}")
else:
    st.error("資料庫連線中...請稍後再試。")
