import streamlit as st
import pandas as pd
import requests
import fitz
import streamlit.components.v1 as components
import base64
import time
import math

# ==========================================
# 【編號 1】頁面設定
# ==========================================
st.set_page_config(page_title="會考自然-理化出師旗艦版", page_icon="🧪", layout="wide")

st.markdown("""
    <style>
    #MainMenu, header, footer {visibility: hidden;}
    .stApp { background-color: #ffffff; }
    html, body, [class*="css"], p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
    }
    .block-container { padding: 1rem 0rem !important; max-width: 100% !important; }
    @media (min-width: 1024px) {
        .block-container { padding-left: 2rem !important; padding-right: 2rem !important; } 
        div[data-baseweb="select"] { font-size: 24px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 【編號 2】資料讀取與快取
# ==========================================
@st.cache_data(ttl=3600)
def load_data_fresh():
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
    try: return pd.read_csv(SHEET_URL)
    except: return None

@st.cache_data(show_spinner=False)
def get_pdf_page_as_base64(local_pdf_path, page_index):
    try:
        doc = fitz.open(local_pdf_path)
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        img_data = pix.tobytes("png"); doc.close()
        return base64.b64encode(img_data).decode('utf-8')
    except: return ""

@st.cache_data(show_spinner=False)
def get_script_json(json_url):
    try:
        res = requests.get(json_url, timeout=5)
        if res.status_code == 200: return res.text
    except: pass
    return "[]"

# ==========================================
# 【編號 3】控制介面
# ==========================================
df = load_data_fresh()
if df is not None and not df.empty:
    if 'page_idx' not in st.session_state: st.session_state.page_idx = 0
    total_items = len(df); group_size = 10
    
    c_group, c_unit, c_speed, c_size = st.columns([1.5, 1.7, 1.0, 1.8])
    with c_group:
        sel_group = st.selectbox("範圍", [f"進度 {i*10+1}~{min((i+1)*10, total_items)}" for i in range(math.ceil(total_items/10))], index=st.session_state.page_idx // 10, label_visibility="collapsed")
        new_g_idx = [f"進度 {i*10+1}~{min((i+1)*10, total_items)}" for i in range(math.ceil(total_items/10))].index(sel_group)
        if new_g_idx != st.session_state.page_idx // 10:
            st.session_state.page_idx = new_g_idx * 10; st.rerun()

    with c_unit:
        start_idx = (st.session_state.page_idx // 10) * 10
        unit_list = df.iloc[start_idx:min(start_idx+10, total_items)]['Title'].tolist()
        sel_unit = st.selectbox("單元", unit_list, index=st.session_state.page_idx % 10, label_visibility="collapsed")
        st.session_state.page_idx = start_idx + unit_list.index(sel_unit)
            
    with c_speed:
        spd_opt = {"1.0x": 1.0, "1.25x": 1.25, "1.5x": 1.5, "2.0x": 2.0}
        play_speed = spd_opt[st.selectbox("語速", list(spd_opt.keys()), index=0, label_visibility="collapsed")]
        
    with c_size:
        sz_opt = {"電視霸氣": "clamp(32px, 5vw, 100px)", "標準教學": "clamp(24px, 3.5vw, 65px)", "手機隨身": "clamp(18px, 5vmin, 36px)"}
        bubble_fs = sz_opt[st.selectbox("字幕大小", list(sz_opt.keys()), index=0, label_visibility="collapsed")]

    row = df.iloc[st.session_state.page_idx]
    pdf_page = int(str(row['頁碼']).strip()) - 1 if '頁碼' in df.columns else 0
    audio_path = str(row['Audio_Path']).strip().lstrip('/')
    audio_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path}?t={time.time()}"
    json_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path.replace('.mp3', '_script.json')}"
    pdf_b64 = get_pdf_page_as_base64("notes.pdf", max(0, pdf_page))
    script_data = get_script_json(json_url)

# ==========================================
# 【編號 5】HTML/JS (防閃爍 + 黃金排版定位)
# ==========================================
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
    <style>
        body {{ font-family: sans-serif; margin: 0; padding: 0; background: white; }}
        .header-bar {{ display: flex; align-items: center; justify-content: space-between; padding: 10px 20px; border-bottom: 1px solid #eee; }}
        .title {{ color: #1d4ed8; font-size: 24px; font-weight: bold; }}
        .btn {{ background: #1d4ed8; color: white; padding: 10px 20px; border-radius: 50px; border: none; cursor: pointer; font-weight: bold; margin-left: 5px; }}
        
        .pdf-view {{ position: relative; width: 100%; overflow: hidden; }}
        .pdf-img {{ width: 100%; display: block; }}
        
        /* 💬 對話區 (置底) */
        .subtitle-stage {{ position: absolute; bottom: 8%; width: 100%; display: flex; flex-direction: column; padding: 0 40px; box-sizing: border-box; pointer-events: none; z-index: 10; }}
        .bubble {{ 
            max-width: 85%; padding: 15px 25px; border-radius: 20px; font-size: {bubble_fs}; 
            opacity: 0; transition: opacity 0.3s; font-weight: bold; box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .yanjun {{ align-self: flex-start; background: rgba(235, 245, 255, 0.95); color: #004085; border: 2px solid #b8daff; }}
        .xiaozhen {{ align-self: flex-end; background: rgba(255, 245, 245, 0.95); color: #721c24; border: 2px solid #f5c6cb; }}
        .chorus {{ align-self: center; background: #fffde7; color: #856404; border: 2px solid #fde68a; }}

        /* 📌 黑板算式區 (防閃爍、完美對齊彥君字幕) */
        .board-stage {{ 
            position: absolute; 
            bottom: calc(8% + {bubble_fs} * 2.5); /* 動態計算，永遠貼在對話框正上方 */
            left: 40px; /* 和主字幕相同的 padding 邊距 */
            display: flex; flex-direction: column; gap: 10px; pointer-events: none; z-index: 5;
        }}
        .board-item {{
            background: rgba(240, 248, 255, 0.9); /* 淺藍色半透明，融合彥君氣泡色系 */
            color: #0d47a1; /* 深藍色字體 */
            padding: 10px 20px; border-radius: 12px;
            font-size: calc({bubble_fs} * 0.85); font-weight: bold;
            border-left: 5px solid #1d4ed8;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            margin-left: calc({bubble_fs} * 1.8); /* 🚀 關鍵：扣掉頭像表情符號的寬度，讓文字完美對齊 */
            animation: fadeIn 0.4s ease-out forwards;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .seek-panel {{ width: 100%; background: #f8f9fa; padding: 10px 20px; display: flex; align-items: center; gap: 15px; box-sizing: border-box; }}
        input[type=range] {{ flex: 1; }}
        body.theater {{ background: #000; }}
        body.theater .header-bar, body.theater .seek-panel {{ background: #111; color: #eee; border: none; }}
        
        @media (max-width: 768px) {{
            .subtitle-stage {{ bottom: 3%; padding: 0 10px; }}
            .board-stage {{ left: 10px; bottom: calc(3% + {bubble_fs} * 3); }}
            .board-item {{ margin-left: calc({bubble_fs} * 2); }}
        }}
    </style>
    </head>
    <body>
        <div class="header-bar">
            <div class="title">🚀 理化特攻隊旗艦版</div>
            <div><button id="fsBtn" class="btn">🔲 全螢幕</button><button id="pBtn" class="btn">▶️ 收聽</button></div>
        </div>
        <audio id="aud" src="{audio_url}"></audio>
        <div class="pdf-view">
            <img src="data:image/png;base64,{pdf_b64}" class="pdf-img">
            <div id="board-stage" class="board-stage"></div> <div class="subtitle-stage"><div id="bubble" class="bubble"><span id="msg"></span></div></div>
        </div>
        <div class="seek-panel">
            <input type="range" id="sk" value="0" step="0.1">
            <div style="min-width:100px"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
        </div>
        <script>
            const aud = document.getElementById('aud');
            const pBtn = document.getElementById('pBtn');
            const fsBtn = document.getElementById('fsBtn');
            const sk = document.getElementById('sk');
            const boardStage = document.getElementById('board-stage');
            const bubble = document.getElementById('bubble');
            const msg = document.getElementById('msg');
            const script = {script_data};
            
            let lastMsgHash = "";

            aud.playbackRate = {play_speed};
            pBtn
