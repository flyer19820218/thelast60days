import streamlit as st
import pandas as pd
import requests
import fitz
import streamlit.components.v1 as components
import base64
import time
import math

# ==========================================
# 【編號 1】頁面設定與 RWD 響應式 CSS
# ==========================================
st.set_page_config(page_title="會考自然-旗艦教學版", page_icon="📚", layout="wide")

st.markdown("""
    <style>
    #MainMenu, header, footer {visibility: hidden;}
    .stApp { background-color: #ffffff; }
    html, body, [class*="css"], p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        padding-bottom: 0rem !important;
        max-width: 100% !important;
    }
    
    /* 📺【大電視霸氣模式設定】 */
    @media (min-width: 1024px) {
        .block-container { padding-left: 2rem !important; padding-right: 2rem !important; } 
        div[data-baseweb="select"] { font-size: 24px !important; }
        div[data-baseweb="select"] > div { min-height: 55px !important; }
        .stButton > button { font-size: 24px !important; min-height: 55px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 【編號 2】資料讀取與快取
# ==========================================
@st.cache_data(ttl=3600)
def load_data_fresh():
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
    try:
        return pd.read_csv(SHEET_URL)
    except:
        return None

@st.cache_data(show_spinner=False)
def get_pdf_page_as_base64(local_pdf_path, page_index):
    try:
        doc = fitz.open(local_pdf_path)
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)) 
        img_data = pix.tobytes("png")
        doc.close()
        return base64.b64encode(img_data).decode('utf-8')
    except:
        return ""

@st.cache_data(show_spinner=False)
def get_script_json(json_url):
    try:
        res = requests.get(json_url, timeout=5)
        if res.status_code == 200:
            return res.text
    except:
        pass
    return "[]"

# ==========================================
# 【編號 3】控制介面
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

    c_group, c_unit, c_speed, c_size = st.columns([1.5, 1.7, 1.0, 1.8])
    
    with c_group:
        selected_group = st.selectbox("範圍", group_labels, index=current_group_idx, label_visibility="collapsed")
        new_group_idx = group_labels.index(selected_group)
        if new_group_idx != current_group_idx:
            st.session_state.page_idx = new_group_idx * group_size
            st.rerun()

    with c_unit:
        start_idx = new_group_idx * group_size
        sub_df = df.iloc[start_idx:min(start_idx + group_size, total_items)]
        unit_list = sub_df['Title'].tolist()
        local_idx = st.session_state.page_idx - start_idx
        selected_day = st.selectbox("單元", unit_list, index=local_idx if local_idx < len(unit_list) else 0, label_visibility="collapsed")
        st.session_state.page_idx = start_idx + unit_list.index(selected_day)
            
    with c_speed:
        speed_options = {"正常 1.0x": 1.0, "微快 1.25x": 1.25, "衝刺 1.5x": 1.5}
        selected_speed_label = st.selectbox("語速", list(speed_options.keys()), index=0, label_visibility="collapsed")
        play_speed = speed_options[selected_speed_label]
        
    with c_size:
        size_options = {
            "電視霸氣": "clamp(32px, 5vw, 100px)",
            "標準教學": "clamp(24px, 3.5vw, 65px)",
            "手機隨身": "clamp(18px, 5vmin, 36px)"
        }
        bubble_fs = size_options[st.selectbox("字幕大小", list(size_options.keys()), index=0, label_visibility="collapsed")]

    main_container = st.empty()

# ==========================================
# 【編號 4】資料解析
# ==========================================
    try:
        row = df.iloc[st.session_state.page_idx]
        pdf_page_idx = int(str(row['頁碼']).strip()) - 1 if '頁碼' in df.columns else 0
        audio_path = str(row['Audio_Path']).strip().lstrip('/')
        audio_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path}?t={time.time()}"
        json_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path.replace('.mp3', '_script.json')}"
        pdf_b64 = get_pdf_page_as_base64("notes.pdf", pdf_page_idx if pdf_page_idx >= 0 else 0)
        script_data = get_script_json(json_url)

# ==========================================
# 【編號 5】HTML/JS 核心核心 (雙軌不塞車 + 無泡泡板書)
# ==========================================
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{ font-family: sans-serif; margin: 0; padding: 0; background: white; }}
            .header-bar {{ display: flex; align-items: center; justify-content: space-between; padding: 10px 20px; border-bottom: 1px solid #eee; }}
            .title {{ color: #1d4ed8; font-size: 24px; font-weight: bold; }}
            .play-btn, .fs-btn {{ background: #1d4ed8; color: white; padding: 10px 20px; border-radius: 50px; border: none; cursor: pointer; font-weight: bold; margin-left: 5px; }}
            
            .pdf-view {{ position: relative; width: 100%; }}
            .pdf-img {{ width: 100%; display: block; }}
            
            /* 💬 軌道 A：對話區 (有泡泡) */
            .subtitle-stage {{ position: absolute; bottom: 8%; width: 100%; display: flex; flex-direction: column; padding: 0 40px; box-sizing: border-box; pointer-events: none; }}
            .bubble {{ 
                max-width: 85%; padding: 15px 25px; border-radius: 20px; font-size: {bubble_fs}; 
                opacity: 0; transition: 0.3s; font-weight: bold; box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }}
            .yanjun {{ align-self: flex-start; background: rgba(235, 245, 255, 0.9); color: #004085; border: 2px solid #b8daff; }}
            .xiaozhen {{ align-self: flex-end; background: rgba(FFF5F5, 0.9); color: #721c24; border: 2px solid #f5c6cb; }}
            .chorus {{ align-self: center; background: linear-gradient(to bottom, #fff, #ffeeba); color: #856404; border: 2px solid #ffeeba; }}

            /* 📌 軌道 B：黑板區 (無泡泡，專業手寫感) */
            .board-stage {{ position: absolute; top: 10%; right: 5%; display: flex; flex-direction: column; gap: 15px; max-width: 40%; pointer-events: none; }}
            .board-item {{
                background: rgba(0, 0, 0, 0.6); /* 半透明深色底，像黑板 */
                color: #ffeb3b; /* 亮黃色，像重點粉筆 */
                padding: 10px 20px; border-radius: 8px;
                font-size: calc({bubble_fs} * 0.85);
                font-family: 'Courier New', Courier, monospace; /* 字體更有科技/算式感 */
                border-left: 5px solid #ffeb3b;
                box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
                animation: slideIn 0.5s ease-out forwards;
            }}
            @keyframes slideIn {{ from {{ opacity: 0; transform: translateX(30px); }} to {{ opacity: 1; transform: translateX(0); }} }}

            .seek-panel {{ width: 100%; background: #f8f9fa; padding: 10px 20px; display: flex; align-items: center; gap: 15px; box-sizing: border-box; }}
            input[type=range] {{ flex: 1; cursor: pointer; }}
        </style>
        </head>
        <body>
            <div class="header-bar">
                <div class="title">🚀 理化特攻隊</div>
                <div><button id="fsBtn" class="fs-btn">🔲 全螢幕</button><button id="pBtn" class="play-btn">▶️ 立刻收聽</button></div>
            </div>
            <audio id="aud" src="{audio_url}"></audio>
            <div class="pdf-view">
                <img src="data:image/png;base64,{pdf_b64}" class="pdf-img">
                <div id="board-stage" class="board-stage"></div> <div class="subtitle-stage"><div id="bubble" class="bubble"><span id="msg"></span></div></div> </div>
            <div class="seek-panel">
                <input type="range" id="sk" value="0" step="0.1">
                <div style="min-width:100px"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
            </div>
            <script>
                const aud = document.getElementById('aud');
                const pBtn = document.getElementById('pBtn');
                const sk = document.getElementById('sk');
                const boardStage = document.getElementById('board-stage');
                const bubble = document.getElementById('bubble');
                const msg = document.getElementById('msg');
                const script = {script_data};
                
                aud.playbackRate = {play_speed};
                pBtn.onclick = () => {{ if(aud.paused) {{ aud.play(); pBtn.innerText="⏸️ 暫停"; }} else {{ aud.pause(); pBtn.innerText="▶️ 收聽"; }} }};
                aud.onloadedmetadata = () => {{ document.getElementById('dur').innerText = fmt(aud.duration); sk.max = aud.duration; }};
                
                // 🚀 關鍵：雙軌處理邏輯
                aud.ontimeupdate = () => {{
                    const t = aud.currentTime;
                    sk.value = t;
                    document.getElementById('cur').innerText = fmt(t);
                    
                    let mainSub = null;
                    let pinnedItems = [];

                    // 1. 分流資料
                    script.forEach(s => {{
                        if (t >= s.start) {{
                            if (s.is_pinned === true) {{
                                pinnedItems.push(s); // 只要開始時間到了，就放進黑板
                            }} else if (t <= s.end) {{
                                mainSub = s; // 一般對話要在時間區間內才抓
                            }}
                        }}
                    }});

                    // 2. 顯示一般對話 (有泡泡)
                    if (mainSub) {{
                        msg.innerText = (mainSub.speaker === '彥君' ? '👨‍🏫 ' : '👩‍🔬 ') + mainSub.text;
                        bubble.className = "bubble " + (mainSub.speaker === '彥君' ? 'yanjun' : 'xiaozhen');
                        bubble.style.opacity = 1;
                    }} else {{ bubble.style.opacity = 0; }}

                    // 3. 顯示釘選黑板 (無泡泡，堆疊式)
                    boardStage.innerHTML = ''; 
                    pinnedItems.forEach(item => {{
                        const div = document.createElement('div');
                        div.className = 'board-item';
                        div.innerText = item.text;
                        boardStage.appendChild(div);
                    }});
                }};
                
                function fmt(s) {{ return Math.floor(s/60) + ":" + String(Math.floor(s%60)).padStart(2,'0'); }}
                sk.oninput = () => aud.currentTime = sk.value;
            </script>
        </body>
        </html>
        """
        with main_container: components.html(full_html, height=1200, scrolling=True)
    except Exception as e: st.error(f"錯誤：{e}")
