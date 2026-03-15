import streamlit as st
import pandas as pd
import requests
import fitz
import streamlit.components.v1 as components
import base64
import time
import math

# ==========================================
# 1. 基礎設定與快取
# ==========================================
st.set_page_config(page_title="會考自然-旗艦教學版", layout="wide")

# 隱藏預設介面
st.markdown("""
    <style>
    #MainMenu, header, footer {visibility: hidden;}
    .stApp { background-color: #ffffff; }
    html, body, p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
    }
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
        pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0)) 
        img_data = pix.tobytes("png")
        doc.close()
        return base64.b64encode(img_data).decode('utf-8')
    except:
        return ""

# ==========================================
# 2. 資料讀取
# ==========================================
df = load_data_fresh()

if df is not None and not df.empty:
    if 'page_idx' not in st.session_state:
        st.session_state.page_idx = 0

    total_items = len(df)
    group_size = 10
    num_groups = math.ceil(total_items / group_size)
    group_labels = [f"進度 {i*group_size + 1} ~ {min((i+1)*group_size, total_items)}" for i in range(num_groups)]
    current_group_idx = st.session_state.page_idx // group_size

    # --- 頂部控制列 ---
    c_group, c_unit, c_speed, c_prev, c_next = st.columns([1.5, 3.5, 1.0, 0.5, 0.5])
    
    with c_group:
        selected_group = st.selectbox("範圍", group_labels, index=current_group_idx, label_visibility="collapsed")
        new_group_idx = group_labels.index(selected_group)
        if new_group_idx != current_group_idx:
            st.session_state.page_idx = new_group_idx * group_size
            st.rerun()

    with c_unit:
        start_idx = new_group_idx * group_size
        end_idx = min(start_idx + group_size, total_items)
        sub_df = df.iloc[start_idx:end_idx]
        unit_list = sub_df['Title'].tolist()
        local_idx = st.session_state.page_idx - start_idx
        selected_day = st.selectbox("單元", unit_list, index=local_idx, label_visibility="collapsed")
        new_local_idx = unit_list.index(selected_day)
        if new_local_idx != local_idx:
            st.session_state.page_idx = start_idx + new_local_idx
            st.rerun()
            
    with c_speed:
        speed_options = {"正常 1.0x": 1.0, "微快 1.25x": 1.25, "衝刺 1.5x": 1.5, "超光速 2.0x": 2.0}
        selected_speed_label = st.selectbox("語速", list(speed_options.keys()), index=0, label_visibility="collapsed")
        play_speed = speed_options[selected_speed_label]
    
    with c_prev:
        if st.button("⬅️"):
            st.session_state.page_idx = max(0, st.session_state.page_idx - 1)
            st.rerun()
    with c_next:
        if st.button("➡️"):
            st.session_state.page_idx = min(total_items - 1, st.session_state.page_idx + 1)
            st.rerun()

    # ==========================================
    # 3. 核心畫面處理
    # ==========================================
    row = df.iloc[st.session_state.page_idx]
    try:
        pdf_page_idx = int(str(row['頁碼']).strip()) - 1
        if pdf_page_idx < 0: pdf_page_idx = 0
    except:
        pdf_page_idx = 0

    audio_path = str(row['Audio_Path']).strip().lstrip('/')
    audio_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path}?t={time.time()}"
    json_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path.replace('.mp3', '_script.json')}?t={time.time()}"
    
    pdf_b64 = get_pdf_page_as_base64("notes.pdf", pdf_page_idx)
    res_json = requests.get(json_url)
    script_data = res_json.text if res_json.status_code == 200 else "[]"

    # 🌟 注入 YouTuber 字幕樣式
    st.markdown("""
        <style>
        .header-bar { position: fixed; top: 0; width: 100%; z-index: 100; display: flex; align-items: center; justify-content: space-between; padding: 10px 20px; background: rgba(255,255,255,0.9); box-shadow: 0 2px 10px rgba(0,0,0,0.3); }
        .title { color: #1d4ed8; font-size: 24px; font-weight: bold; margin: 0; }
        .play-btn { background: #ff0000; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; cursor: pointer; border: none; }
        .pdf-container { margin-top: 60px; margin-bottom: 150px; width: 100%; }
        .pdf-img { width: 100%; display: block; }
        .bottom-console { position: fixed; bottom: 0; width: 100%; background: rgba(0, 0, 0, 0.9); color: white; padding: 15px 0; z-index: 100; display: flex; flex-direction: column; align-items: center; min-height: 120px; }
        .seek-panel { width: 90%; display: flex; align-items: center; gap: 15px; margin-bottom: 10px; }
        input[type=range] { flex: 1; accent-color: #ff0000; cursor: pointer; }
        .subtitle-text { font-size: 32px; font-weight: bold; text-align: center; min-height: 50px; text-shadow: 2px 2px 4px rgba(0,0,0,1); padding: 0 20px; line-height: 1.4; }
        .speaker-label { font-size: 18px; color: #ffff00; margin-bottom: 5px; font-weight: bold; }
        .highlight { color: #ffff00; }
        </style>
        """, unsafe_allow_html=True)

    # 🌟 HTML 模板替換法 (最穩！)
    html_template = """
    <!DOCTYPE html>
    <html>
    <body>
        <div class="header-bar">
            <div class="title">🎬 考前60天：@TITLE@</div>
            <button id="pBtn" class="play-btn">▶️ 播放影片</button>
        </div>
        <audio id="aud" src="@AUDIO_URL@" preload="auto"></audio>
        <div class="pdf-container">
            <img src="data:image/png;base64,@PDF_B64@" class="pdf-img">
        </div>
        <div class="bottom-console">
            <div class="seek-panel">
                <input type="range" id="sk" value="0" step="0.1">
                <div style="font-size:14px;"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
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
            aud.onloadedmetadata = () => {
                document.getElementById('dur').innerText = fmt(aud.duration);
                sk.max = aud.duration;
            };
            aud.ontimeupdate = () => {
                const t = aud.currentTime;
                document.getElementById('cur').innerText = fmt(t);
                sk.value = t;
                let hit = false;
                for(let s of script) {
                    if(t >= s.start && t <= s.end) {
                        spk.innerText = (s.speaker === '彥君' ? '👨‍🏫 彥君老師' : '👩‍🔬 曉臻助教');
                        let processedText = s.text.replace(/『/g, '<span class="highlight">').replace(/』/g, '</span>');
                        msg.innerHTML = processedText;
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
    
    full_html = html_template.replace("@TITLE@", row['Title']) \
                             .replace("@AUDIO_URL@", audio_url) \
                             .replace("@PDF_B64@", pdf_b64) \
                             .replace("@SCRIPT_DATA@", script_data) \
                             .replace("@PLAY_SPEED@", str(play_speed))

    components.html(full_html, height=1800, scrolling=True)

else:
    st.error("Google Sheet 資料連線失敗。")
