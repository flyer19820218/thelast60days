import streamlit as st
import pandas as pd
import requests
import fitz
import streamlit.components.v1 as components
import base64
import time
import math

# ==========================================
# 1. 頁面設定 (針對 16:9 大螢幕優化)
# ==========================================
st.set_page_config(page_title="會考自然-80吋電視旗艦版", layout="wide")

st.markdown("""
    <style>
    #MainMenu, header, footer {visibility: hidden;}
    .stApp { background-color: #000000; } /* 電視版用深色背景，減少眼睛疲勞 */
    html, body, p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
    }
    /* 讓內容區完全滿版 */
    .block-container { padding: 0rem !important; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_data_fresh():
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
    try:
        return pd.read_csv(SHEET_URL)
    except:
        return None

def get_pdf_page_as_base64(local_pdf_path, page_index):
    try:
        doc = fitz.open(local_pdf_path)
        page = doc.load_page(page_index)
        # 🌟 電視版 Matrix 設為 1.2，兼顧清晰度與投影比例
        pix = page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2)) 
        img_data = pix.tobytes("png")
        doc.close()
        return base64.b64encode(img_data).decode('utf-8')
    except:
        return ""

# ==========================================
# 2. 佈局實作
# ==========================================
df = load_data_fresh()

if df is not None and not df.empty:
    if 'page_idx' not in st.session_state:
        st.session_state.page_idx = 0

    total_items = len(df)
    row = df.iloc[st.session_state.page_idx]

    # --- 頂部控制列 (改為深色調，適應大螢幕) ---
    c_unit, c_speed, c_prev, c_next = st.columns([5.0, 1.0, 0.5, 0.5])
    
    with c_unit:
        unit_list = df['Title'].tolist()
        selected_day = st.selectbox("單元", unit_list, index=st.session_state.page_idx, label_visibility="collapsed")
        new_idx = unit_list.index(selected_day)
        if new_idx != st.session_state.page_idx:
            st.session_state.page_idx = new_idx
            st.rerun()
            
    with c_speed:
        speed_options = {"1.0x": 1.0, "1.25x": 1.25, "1.5x": 1.5, "2.0x": 2.0}
        selected_speed_label = st.selectbox("速度", list(speed_options.keys()), index=0, label_visibility="collapsed")
        play_speed = speed_options[selected_speed_label]
    
    with c_prev:
        if st.button("⬅️"):
            st.session_state.page_idx = max(0, st.session_state.page_idx - 1)
            st.rerun()
    with c_next:
        if st.button("➡️"):
            st.session_state.page_idx = min(total_items - 1, st.session_state.page_idx + 1)
            st.rerun()

    # 資料處理
    pdf_page_idx = int(str(row['頁碼']).strip()) - 1 if '頁碼' in row else 0
    audio_path = str(row['Audio_Path']).strip().lstrip('/')
    audio_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path}?t={time.time()}"
    json_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path.replace('.mp3', '_script.json')}?t={time.time()}"
    
    pdf_b64 = get_pdf_page_as_base64("notes.pdf", max(0, pdf_page_idx))
    res_json = requests.get(json_url)
    script_data = res_json.text if res_json.status_code == 200 else "[]"

    # 🌟 核心：80吋電視專用 CSS
    st.markdown("""
        <style>
        /* 播放按鈕 */
        .play-btn { background: #ff0000; color: white; padding: 12px 30px; border-radius: 5px; font-weight: bold; font-size: 20px; cursor: pointer; border: none; }
        
        /* PDF 顯示區：固定比例，不讓它爆開 */
        .pdf-view { position: relative; width: 100%; text-align: center; background: #000; padding-top: 50px; }
        .pdf-img { height: 80vh; max-width: 100%; margin: 0 auto; display: block; }
        
        /* 🌟 電視專用置底字幕條 (YouTube 質感) */
        .sub-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background: rgba(0, 0, 0, 0.85);
            padding: 20px 0;
            z-index: 1000;
            text-align: center;
            border-top: 2px solid #333;
        }
        .subtitle-text {
            font-size: 36px; /* 80吋電視一定要大字 */
            font-weight: bold;
            color: #ffffff;
            text-shadow: 2px 2px 4px #000;
            line-height: 1.4;
            padding: 0 50px;
        }
        .highlight { color: #ffff00; } /* 亮黃色重點 */
        .speaker { font-size: 18px; color: #aaaaaa; margin-bottom: 5px; }
        
        /* 進度控制條 */
        .seek-container { width: 90%; margin: 0 auto; display: flex; align-items: center; gap: 15px; margin-bottom: 10px; }
        input[type=range] { flex: 1; accent-color: #ff0000; cursor: pointer; }
        </style>
        """, unsafe_allow_html=True)

    html_template = """
    <!DOCTYPE html>
    <html>
    <body style="margin:0; background: black; overflow: hidden;">
        <audio id="aud" src="@AUDIO_URL@" preload="auto"></audio>
        
        <div class="pdf-view">
            <div style="position: absolute; top: 10px; right: 20px; z-index: 1001;">
                <button id="pBtn" class="play-btn">▶️ 播放單元</button>
            </div>
            <img src="data:image/png;base64,@PDF_B64@" class="pdf-img">
        </div>

        <div class="sub-bar">
            <div class="seek-container">
                <input type="range" id="sk" value="0" step="0.1">
                <div style="color: white; font-size: 14px; min-width: 100px;">
                    <span id="cur">0:00</span> / <span id="dur">0:00</span>
                </div>
            </div>
            <div id="spk" class="speaker"></div>
            <div id="msg" class="subtitle-text">準備就緒...</div>
        </div>

        <script>
            const aud = document.getElementById('aud');
            const pBtn = document.getElementById('pBtn');
            const sk = document.getElementById('sk');
            const spk = document.getElementById('spk');
            const msg = document.getElementById('msg');
            const script = @SCRIPT_DATA@;
            
            aud.playbackRate = @PLAY_SPEED@;

            pBtn.onclick = () => {
                if(aud.paused) { aud.play(); pBtn.innerText = "⏸ 暫停"; }
                else { aud.pause(); pBtn.innerText = "▶ 繼續"; }
            };
            
            aud.onloadedmetadata = () => { sk.max = aud.duration; document.getElementById('dur').innerText = fmt(aud.duration); };
            
            aud.ontimeupdate = () => {
                const t = aud.currentTime;
                sk.value = t; document.getElementById('cur').innerText = fmt(t);
                let hit = false;
                for(let s of script) {
                    if(t >= s.start && t <= s.end) {
                        spk.innerText = s.speaker === '彥君' ? '【 彥君老師 】' : '【 曉臻助教 】';
                        msg.innerHTML = s.text.replace(/『/g, '<span class="highlight">').replace(/』/g, '</span>');
                        hit = true; break;
                    }
                }
                if(!hit) { msg.innerText = ""; spk.innerText = ""; }
            };
            
            sk.oninput = () => aud.currentTime = sk.value;
            function fmt(s) { return Math.floor(s/60) + ":" + String(Math.floor(s%60)).padStart(2,'0'); }
        </script>
    </body>
    </html>
    """
    
    full_html = html_template.replace("@TITLE@", row['Title']).replace("@AUDIO_URL@", audio_url).replace("@PDF_B64@", pdf_b64).replace("@SCRIPT_DATA@", script_data).replace("@PLAY_SPEED@", str(play_speed))

    components.html(full_html, height=1080, scrolling=False)

else:
    st.error("資料讀取失敗，戰士請重新整理。")
