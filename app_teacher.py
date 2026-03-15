import streamlit as st
import pandas as pd
import requests
import fitz
import streamlit.components.v1 as components
import base64
import time
import math

# ==========================================
# 1. 頁面設定
# ==========================================
st.set_page_config(page_title="會考自然-旗艦教學版", layout="wide")

st.markdown("""
    <style>
    #MainMenu, header, footer {visibility: hidden;}
    .stApp { background-color: #ffffff; }
    /* 🌟 移除所有邊距，確保平板畫面滿版 */
    .block-container { padding: 0rem !important; }
    iframe { border: none !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 資料與 PDF 處理 (回歸 1.0 原始比例)
# ==========================================
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
        # 🌟 戰士指導：回歸 1.0 倍率，平板解析度剛剛好
        pix = page.get_pixmap(matrix=fitz.Matrix(1.0, 1.0)) 
        img_data = pix.tobytes("png")
        doc.close()
        return base64.b64encode(img_data).decode('utf-8')
    except:
        return ""

# ==========================================
# 3. 佈局與邏輯
# ==========================================
df = load_data_fresh()

if df is not None and not df.empty:
    if 'page_idx' not in st.session_state:
        st.session_state.page_idx = 0

    total_items = len(df)
    row = df.iloc[st.session_state.page_idx]
    
    # 頂部控制列 (為了平板操作方便，按鈕稍微加大)
    c_group, c_unit, c_speed, c_prev, c_next = st.columns([1.5, 3.5, 1.0, 0.5, 0.5])
    
    with c_group:
        group_size = 10
        num_groups = math.ceil(total_items / group_size)
        group_labels = [f"進度 {i*group_size + 1} ~ {min((i+1)*group_size, total_items)}" for i in range(num_groups)]
        selected_group = st.selectbox("範圍", group_labels, index=st.session_state.page_idx // group_size, label_visibility="collapsed")
        
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

    # 🌟 注入 CSS (平板 100% 寬度優化)
    st.markdown("""
        <style>
        .header-bar { position: fixed; top: 0; width: 100%; z-index: 100; display: flex; align-items: center; justify-content: space-between; padding: 10px 20px; background: rgba(255,255,255,0.95); }
        .title { color: #1d4ed8; font-size: 20px; font-weight: bold; }
        .play-btn { background: #ff0000; color: white; padding: 10px 20px; border-radius: 5px; border: none; font-weight: bold; }
        
        /* 🌟 讓圖片寬度剛好等於螢幕寬度，絕對不爆框 */
        .pdf-container { margin-top: 50px; margin-bottom: 130px; width: 100vw; text-align: center; }
        .pdf-img { width: 100%; height: auto; display: block; }
        
        .bottom-console { position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(0, 0, 0, 0.9); color: white; padding: 10px 0; z-index: 100; display: flex; flex-direction: column; align-items: center; }
        .seek-panel { width: 95%; display: flex; align-items: center; gap: 10px; }
        input[type=range] { flex: 1; accent-color: #ff0000; }
        .subtitle-text { font-size: 28px; font-weight: bold; text-align: center; padding: 5px 20px; line-height: 1.3; color: white; }
        .speaker-label { font-size: 16px; color: #ffff00; font-weight: bold; }
        .highlight { color: #ffff00; }
        </style>
        """, unsafe_allow_html=True)

    html_template = """
    <!DOCTYPE html>
    <html>
    <body style="margin:0; background: white;">
        <div class="header-bar">
            <div class="title">🎬 @TITLE@</div>
            <button id="pBtn" class="play-btn">▶️ 播放</button>
        </div>
        <audio id="aud" src="@AUDIO_URL@" preload="auto"></audio>
        <div class="pdf-container"><img src="data:image/png;base64,@PDF_B64@" class="pdf-img"></div>
        <div class="bottom-console">
            <div class="seek-panel">
                <input type="range" id="sk" value="0" step="0.1">
                <div style="font-size:12px;"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
            </div>
            <div id="spk" class="speaker-label"></div>
            <div id="msg" class="subtitle-text"></div>
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
                        spk.innerText = (s.speaker === '彥君' ? '👨‍🏫 彥君老師' : '👩‍🔬 曉臻助教');
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

    # 🌟 稍微調整高度，確保平板可以捲動看完整張 PDF
    components.html(full_html, height=1200, scrolling=True)

else:
    st.error("資料讀取失敗，戰士請檢查網路。")
