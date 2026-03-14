import streamlit as st
import pandas as pd
import requests
import fitz  # PyMuPDF

# ==========================================
# 1. 頁面設定
# ==========================================
st.set_page_config(page_title="國中自然60天逆襲", layout="centered")

st.markdown("""
<style>

.main { background-color: #f9f9f9; }

/* 全域字體 */
html, body, [class*="css"], p, span, div {
    font-family: 'HanziPen SC','翩翩體','PingFang TC','Microsoft JhengHei',sans-serif !important;
}

/* 聊天容器 */
.chat-container{
    max-height:500px;
    overflow-y:auto;
    padding:10px;
}

/* 對話泡泡 */
.bubble{
    padding:12px 16px;
    border-radius:20px;
    margin:8px 0;
    max-width:75%;
    font-size:18px;
    line-height:1.6;
}

/* 左側 */
.left{
    background:#ffffff;
    border:1px solid #ddd;
    margin-right:auto;
}

/* 右側 */
.right{
    background:#DCF8C6;
    margin-left:auto;
}

/* 名字 */
.name{
    font-size:13px;
    color:#666;
    margin-bottom:4px;
}

</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Github 設定
# ==========================================
USER = "flyer19820218"
REPO = "thelast60days"
GITHUB_RAW = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/"

# ==========================================
# 3. 讀取 Google Sheet
# ==========================================
@st.cache_data(ttl=60)
def load_data():

    SHEET_URL = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"

    try:
        df = pd.read_csv(SHEET_URL)
        return df
    except:
        return None


# ==========================================
# 4. PDF 轉圖片
# ==========================================
@st.cache_data(ttl=3600)
def get_pdf_page_image(local_pdf_path, page_index):

    try:

        doc = fitz.open(local_pdf_path)

        if page_index >= doc.page_count:
            doc.close()
            return "PAGE_OUT_OF_RANGE"

        page = doc.load_page(page_index)

        pix = page.get_pixmap(matrix=fitz.Matrix(2.0,2.0))

        img_data = pix.tobytes("png")

        doc.close()

        return img_data

    except Exception as e:
        return str(e)


# ==========================================
# 5. 主介面
# ==========================================
st.title("🎧 自然科學真理 PODCAST")
st.caption("免登入、免 API，直接開啟衝刺模式")

df = load_data()

if df is not None:

    unit_list = df['Day'].tolist()

    selected = st.selectbox("📅 選擇今日進度", unit_list)

    row = df[df['Day']==selected].iloc[0]

    st.divider()

    st.header(f"📍 {row['Title']}")

    # ======================================
    # 音訊區
    # ======================================

    st.subheader("🔊 聽講區")

    audio_path = str(row['Audio_Path']).strip()

    if audio_path.startswith('/'):
        audio_path = audio_path[1:]

    audio_url = f"{GITHUB_RAW}{audio_path}"

    st.audio(audio_url)


    # ======================================
    # PDF 講義
    # ======================================

    st.divider()

    st.subheader("📝 彥君老師手繪講義")

    page = st.number_input("翻頁",min_value=1,value=1)

    local_pdf_path = "notes.pdf"

    with st.spinner("載入講義中..."):

        result = get_pdf_page_image(local_pdf_path,page-1)

        if result == "PAGE_OUT_OF_RANGE":

            st.warning("沒有這一頁")

        elif isinstance(result,bytes):

            st.image(result,use_container_width=True)

        else:

            st.error(result)


    # ======================================
    # 對話字幕
    # ======================================

    st.divider()

    st.subheader("💬 衝刺劇本")

    script_path = str(row['Script_Path']).strip()

    if script_path.startswith('/'):
        script_path = script_path[1:]

    script_url = f"{GITHUB_RAW}{script_path}"

    try:

        res = requests.get(script_url)

        res.encoding = "utf-8"

        lines = res.text.split("\n")

        chat_data = []

        current_speaker = "system"

        buffer = []


        def flush_buffer():

            if buffer:

                chat_data.append({
                    "role":current_speaker,
                    "content":"<br>".join(buffer)
                })

                buffer.clear()


        for line in lines:

            line=line.strip()

            if not line:
                continue

            if "彥君" in line and len(line)<=20 and "：" not in line:

                flush_buffer()

                current_speaker="彥君"

            elif "曉臻" in line and len(line)<=20 and "：" not in line:

                flush_buffer()

                current_speaker="曉臻"

            elif "：" in line and ("彥君" in line.split("：")[0] or "曉臻" in line.split("：")[0]):

                flush_buffer()

                speaker,content=line.split("：",1)

                current_speaker="彥君" if "彥君" in speaker else "曉臻"

                buffer.append(content)

                flush_buffer()

                current_speaker="system"

            else:

                buffer.append(line)

        flush_buffer()


        # ================================
        # HTML泡泡渲染
        # ================================

        html="<div class='chat-container'>"

        for msg in chat_data:

            if msg["role"]=="彥君":

                html+=f"""
                <div class='bubble right'>
                <div class='name'>👨‍🏫 彥君老師</div>
                {msg['content']}
                </div>
                """

            elif msg["role"]=="曉臻":

                html+=f"""
                <div class='bubble left'>
                <div class='name'>👩‍🔬 曉臻助教</div>
                {msg['content']}
                </div>
                """

            else:

                html+=f"""
                <div style='text-align:center;color:#999;font-size:14px;margin:10px 0;'>
                {msg['content']}
                </div>
                """

        html+="</div>"

        st.markdown(html,unsafe_allow_html=True)


    except Exception as e:

        st.error(f"劇本讀取失敗 {e}")

else:

    st.error("資料載入失敗")
