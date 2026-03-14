import streamlit as st
import pandas as pd
import requests
import fitz
import streamlit.components.v1 as components
import base64
import time

st.set_page_config(page_title="會考自然-考前60天衝刺", layout="wide")

st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .stApp { background: #f8fafc; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=5) 
def load_data_raw():
    url = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            from io import StringIO
            return pd.read_csv(StringIO(r.text))
    except:
        pass
    return None

def get_pdf_page_64(pdf_page_index):
    try:
        doc = fitz.open("notes.pdf")
        page = doc.load_page(pdf_page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0)) 
        return base64.b64encode(pix.tobytes("png")).decode('utf-8')
    except Exception as e:
        return ""

df = load_data_raw()

if df is not None and not df.empty:
    # --- 🌟 1. 絕對不卡死的狀態管理 ---
    if 'page_idx' not in st.session_state:
        st.session_state.page_idx = 0

    options = [f"第 {row['頁碼']} 頁 - {row['Title']}" for _, row in df.iterrows()]
    
    # 這是強制更新畫面的 Callback 函數
    def change_page():
        selected = st.session_state.course_dropdown
        st.session_state.page_idx = options.index(selected)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.selectbox(
            "🚀 選擇課程單元：", 
            options, 
            index=st.session_state.page_idx, 
            key="course_dropdown", 
            on_change=change_page  # 只要選單一動，立刻強制執行換頁！
        )

    # --- 🌟 2. 取得對應資料 ---
    row = df.iloc[st.session_state.page_idx]
    
    # 強制把 A 欄的 'p' 清除（以防萬一），並轉為數字
    try:
        page_val = str(row['頁碼']).lower().replace('p', '').strip()
        pdf_page_index = int(page_val) - 1
        if pdf_page_index < 0: pdf_page_index = 0
    except:
        pdf_page_index = 0

    audio_file = str(row['Audio_Path']).strip().lstrip('/')
    json_file = audio_file.replace('.mp3', '_script.json')
    title_text = str(row['Title'])
    
    ts = int(time.time() * 1000)
    base_url = "https://raw.githubusercontent.com/flyer19820218/thelast60days/main"
    
    audio_url = f"{base_url}/{audio_file}?v={ts}"
    json_url = f"{base_url}/{json_file}?v={ts}"
    pdf_b64 = get_pdf_page_64(pdf_page_index)

    res_json = requests.get(json_url)
    script_data = res_json.text if res_json.status_code == 200 else "[]"

    # --- 🌟 3. 系統偵測雷達 (給我們看除錯用的) ---
    st.info(f"🔧 系統偵測：目前正在讀取 `{audio_file}`，準備顯示 PDF 第 `{pdf_page_index + 1}` 頁")

    # --- 🌟 4. HTML 播放器 ---
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ font-family: sans-serif; margin: 0; padding: 0; background: white; }}
        .top-bar {{ display: flex; justify-content: space-between; align-items: center; padding: 20px 40px; background: #1e40af; color: white; border-radius: 10px 10px 0 0; }}
        .title {{ font-size: 30px; font-weight: bold; }}
        .play-btn {{ background: white; color: #1e40af; padding: 10px 30px; border-radius: 30px; border: none; font-size: 24px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }}
        .pdf-view {{ width: 100%; border-left: 2px solid #e2e8f0; border-right: 2px solid #e2e8f0; }}
        .pdf-img {{ width: 100%; display: block; }}
        .seek-panel {{ width: 100%; background: #f1f5f9; padding: 25px 40px; display: flex; align-items: center; gap: 20px; box-sizing: border-box; border-left: 2px solid #e2e8f0; border-right: 2px solid #e2e8f0; }}
        input[type=range] {{ flex: 1; accent-color: #1e40af; height: 22px; cursor: pointer; }}
        .time-box {{ font-size: 24px; color: #1e293b; min-width: 140px; text-align: right; font-family: monospace; font-weight: bold; }}
        .subtitle-stage {{ width: 100%; min-height: 240px; display: flex; flex-direction: column; padding: 40px; box-sizing: border-box; border: 2px solid #e2e8f0; border-top: none; border-radius: 0 0 10px 10px; background: #fafafa; }}
        .bubble {{ max-width: 85%; padding: 30px; border-radius: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); font-size: 36px; line-height: 1.5; opacity: 0; transition: 0.2s ease; }}
        .yj {{ align-self: flex-start; background: #e0f2fe; color: #0369a1; border: 2px solid #bae6fd; }}
        .xz {{ align-self: flex-end; background: #fff1f2; color: #be123c; border: 2px solid #fecdd3; }}
    </style>
    </head>
    <body>
        <div class="top-bar">
            <div class="title">📖 {title_text}</div>
            <button id="pBtn" class="play-btn">▶️ 開始講解</button>
        </div>
        <audio id="aud" src="{audio_url}" preload="auto"></audio>
        <div class="pdf-view"><img src="data:image/png;base64,{pdf_b64}" class="pdf-img"></div>
        <div class="seek-panel">
            <input type="range" id="sk" value="0" step="0.1">
            <div class="time-box"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
        </div>
        <div class="subtitle-stage"><div id="bb" class="bubble yj"></div></div>

        <script>
            const aud = document.getElementById('aud');
            const pBtn = document.getElementById('pBtn');
            const sk = document.getElementById('sk');
            const bb = document.getElementById('bb');
            const script = {script_data};

            pBtn.onclick = () => {{
                if(aud.paused) {{ aud.play(); pBtn.innerText = "⏸️ 暫停"; }}
                else {{ aud.pause(); pBtn.innerText = "▶️ 繼續"; }}
            }};
            aud.onloadedmetadata = () => {{
                document.getElementById('dur').innerText = fmt(aud.duration);
                sk.max = aud.duration;
            }};
            aud.ontimeupdate = () => {{
                const t = aud.currentTime;
                document.getElementById('cur').innerText = fmt(t);
                sk.value = t;
                let hit = false;
                for(let s of script) {{
                    if(t >= s.start && t <= s.end) {{
                        bb.innerText = s.text;
                        bb.className = "bubble " + (s.speaker === '彥君' ? 'yj' : 'xz');
                        bb.style.opacity = 1;
                        hit = true; break;
                    }}
                }}
                if(!hit) bb.style.opacity = 0;
            }};
            sk.oninput = () => aud.currentTime = sk.value;
            function fmt(s) {{ return Math.floor(s/60) + ":" + String(Math.floor(s%60)).padStart(2,'0'); }}
        </script>
    </body>
    </html>
    """
    components.html(full_html, height=2200, scrolling=True)

else:
    st.warning("⚠️ 讀取不到 Google Sheet 資料，請確認表單有內容！")
