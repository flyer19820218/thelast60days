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
    /* 🌟 隱藏 Streamlit 預設介面 */
    #MainMenu, header, footer {visibility: hidden;}
    .stApp { background-color: #ffffff; }
    html, body, p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
    }
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
        # 🌟 平板投影建議使用 1.5 倍率，平衡清晰度與螢幕適配
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)) 
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

    # --- 頂部控制列 ---
    c_group, c_unit, c_speed, c_prev, c_next = st.columns([1.5, 3.5, 1.0, 0.5, 0.5])
    
    with c_unit:
        unit_list = df['Title'].tolist()
        selected_day = st.selectbox("單元", unit_list, index=st.session_state.page_idx, label_visibility="collapsed")
        new_idx = unit_list.index(selected_day)
        if new_idx != st.session_state.page_idx:
            st.session_state.page_idx = new_idx
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

    # 資料準備
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

    # ==========================================
    # 3. HTML/JS 模板 (泡泡浮貼版)
    # ==========================================
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ font-family: sans-serif; margin: 0; padding: 0; background: white; }}
        .header-bar {{ display: flex; align-items: center; justify-content: space-between; padding: 10px 20px; border-bottom: 1px solid #f0f0f0; background: white; }}
        .title {{ color: #1d4ed8; font-size: 28px; font-weight: bold; margin: 0; }}
        .play-btn {{ background: linear-gradient(135deg, #2b58db, #1d4ed8); color: white; padding: 10px 25px; border-radius: 50px; font-weight: bold; font-size: 18px; cursor: pointer; border: none; }}
        
        /* 🌟 PDF 視區設定為相對定位 */
        .pdf-view {{ position: relative; width: 100%; }}
        .pdf-img {{ width: 100%; display: block; }}
        
        .seek-panel {{ width: 100%; background: #fdfdfd; padding: 10px 20px; display: flex; align-items: center; gap: 15px; box-sizing: border-box; border-bottom: 1px solid #eee; }}
        input[type=range] {{ flex: 1; accent-color: #1d4ed8; cursor: pointer; height: 10px; }}
        .time-box {{ font-size: 14px; color: #64748b; min-width: 95px; text-align: right; }}

        /* 🌟 字幕舞台：浮貼在圖片底部 */
        .subtitle-stage {{ 
            position: absolute; 
            bottom: 30px; 
            width: 100%; 
            display: flex; 
            flex-direction: column; 
            padding: 0 40px; 
            box-sizing: border-box; 
            z-index: 10;
        }}
        .bubble {{ 
            max-width: 85%; 
            padding: 15px 25px; 
            border-radius: 20px; 
            box-shadow: 0 8px 32px rgba(0,0,0,0.2); 
            font-size: 28px; 
            line-height: 1.4; 
            opacity: 0; 
            transition: all 0.3s ease; 
            backdrop-filter: blur(8px);
        }}
        .yanjun {{ align-self: flex-start; background-color: rgba(227, 242, 253, 0.9); color: #0d47a1; border: 2px solid #bbdefb; border-bottom-left-radius: 2px; }}
        .xiaozhen {{ align-self: flex-end; background-color: rgba(254, 242, 242, 0.9); color: #991b1b; border: 2px solid #fecaca; border-bottom-right-radius: 2px; }}
        .name {{ font-size: 16px; font-weight: bold; margin-bottom: 5px; }}
    </style>
    </head>
    <body>
        <div class="header-bar">
            <div class="title">🚀 考前60天衝刺</div>
            <button id="pBtn" class="play-btn">▶️立刻收聽</button>
        </div>
        <audio id="aud" src="{audio_url}" preload="auto"></audio>
        
        <div class="pdf-view">
            <img src="data:image/png;base64,{pdf_b64}" class="pdf-img">
            <div class="subtitle-stage">
                <div id="bubble" class="bubble yanjun"><div id="spk" class="name"></div><div id="msg"></div></div>
            </div>
        </div>

        <div class="seek-panel">
            <input type="range" id="sk" value="0" step="0.1">
            <div class="time-box"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
        </div>

        <script>
            const aud = document.getElementById('aud');
            const pBtn = document.getElementById('pBtn');
            const sk = document.getElementById('sk');
            const bubble = document.getElementById('bubble');
            const spk = document.getElementById('spk');
            const msg = document.getElementById('msg');
            const script = {script_data};
            
            aud.playbackRate = {play_speed};

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
                        spk.innerText = (s.speaker === '彥君' ? '👨‍🏫 彥君老師' : '👩‍🔬 曉臻助教');
                        msg.innerText = s.text;
                        bubble.className = "bubble " + (s.speaker === '彥君' ? 'yanjun' : 'xiaozhen');
                        bubble.style.opacity = 1;
                        hit = true; break;
                    }}
                }}
                if(!hit) bubble.style.opacity = 0;
            }};
            sk.oninput = () => aud.currentTime = sk.value;
            function fmt(s) {{ return Math.floor(s/60) + ":" + String(Math.floor(s%60)).padStart(2,'0'); }}
        </script>
    </body>
    </html>
    """
    
    components.html(full_html, height=1500, scrolling=True)

else:
    st.error("Google Sheet 資料連線失敗。")
