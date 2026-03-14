import streamlit as st
import pandas as pd
import requests
import fitz
import streamlit.components.v1 as components
import json
import base64

# ==========================================
# 1. 頁面設定 (寬螢幕教學模式)
# ==========================================
st.set_page_config(page_title="會考自然-旗艦教學版", layout="wide")

st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .stApp { background-color: #f0f2f6; }
    
    /* 強制字體 */
    html, body, [class*="css"], p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
    }
    
    /* 頂部控制列 */
    .control-row {
        background: white;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 資料載入
@st.cache_data(ttl=60)
def load_data():
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
    try:
        return pd.read_csv(SHEET_URL)
    except:
        return None

def get_pdf_page_as_base64(local_pdf_path, page_index):
    try:
        doc = fitz.open(local_pdf_path)
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5)) 
        img_data = pix.tobytes("png")
        doc.close()
        return base64.b64encode(img_data).decode('utf-8')
    except:
        return ""

# ==========================================
# 2. 佈局實作
# ==========================================
df = load_data()

if df is not None:
    # --- 頂部控制列 ---
    st.markdown('<div class="control-row">', unsafe_allow_html=True)
    t1, t2, t3, t4 = st.columns([2.5, 1, 1, 1.5])
    
    unit_list = df['Day'].tolist()
    selected_day = t1.selectbox("今日進度", unit_list, label_visibility="collapsed")
    row = df[df['Day'] == selected_day].iloc[0]
    
    if 'page_num' not in st.session_state: st.session_state.page_num = 1
    
    with t2:
        if st.button("⬅️ 上一頁"): st.session_state.page_num = max(1, st.session_state.page_num - 1)
    with t3:
        if st.button("下一頁 ➡️"): st.session_state.page_num += 1
    with t4:
        st.info(f"📍 目前頁碼: {st.session_state.page_num}")
    st.markdown('</div>', unsafe_allow_html=True)

    # 準備資料
    pdf_b64 = get_pdf_page_as_base64("notes.pdf", st.session_state.page_num - 1)
    audio_path = str(row['Audio_Path']).strip().lstrip('/')
    audio_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path}"
    json_url = audio_url.replace('.mp3', '_script.json')

    try:
        res_json = requests.get(json_url)
        script_data = res_json.text if res_json.status_code == 200 else "[]"

        # --- 🔥 旗艦白金版教學介面 🔥 ---
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{ font-family: sans-serif; margin: 0; padding: 0; background: #f0f2f6; overflow: hidden; }}
            .main-layout {{ display: flex; height: 85vh; gap: 20px; padding: 10px; }}
            
            /* 左側：大講義 */
            .left-panel {{ flex: 2.5; background: white; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); overflow: hidden; display: flex; align-items: center; justify-content: center; }}
            .pdf-img {{ max-height: 100%; max-width: 100%; object-fit: contain; }}

            /* 右側：控制與字幕 */
            .right-panel {{ flex: 1; display: flex; flex-direction: column; gap: 20px; }}
            
            .player-card {{ background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
            .play-btn {{ background: #2b58db; color: white; border: none; padding: 15px; width: 100%; border-radius: 50px; font-weight: bold; font-size: 18px; cursor: pointer; }}
            
            .subtitle-card {{ 
                background: white; flex-grow: 1; padding: 25px; border-radius: 20px; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.05); display: flex; flex-direction: column; 
                justify-content: center; position: relative;
            }}
            .bubble {{ font-size: 26px; line-height: 1.6; text-align: center; opacity: 0; transition: all 0.3s; }}
            .name {{ font-size: 16px; font-weight: bold; margin-bottom: 10px; border-radius: 5px; padding: 5px 10px; display: inline-block; }}
            .yanjun-name {{ background: #e3f2fd; color: #0d47a1; }}
            .xiaozhen-name {{ background: #fef2f2; color: #991b1b; }}
            
            .seek-bar {{ width: 100%; margin-top: 15px; accent-color: #2b58db; }}
        </style>
        </head>
        <body>
            <div class="main-layout">
                <div class="left-panel">
                    <img src="data:image/png;base64,{pdf_b64}" class="pdf-img">
                </div>
                
                <div class="right-panel">
                    <div class="player-card">
                        <button id="pBtn" class="play-btn">▶️ 開始教學演示</button>
                        <input type="range" id="sk" value="0" step="0.1" class="seek-bar">
                        <div style="display:flex; justify-content:space-between; margin-top:8px; font-size:13px; color:#666;">
                            <span id="cur">0:00</span><span id="dur">0:00</span>
                        </div>
                    </div>

                    <div class="subtitle-card">
                        <div id="spkBox" style="text-align:center;"></div>
                        <div id="msg" class="bubble">點擊播放鍵，同步字幕將在此呈現。</div>
                    </div>
                </div>
            </div>

            <audio id="aud" src="{audio_url}"></audio>

            <script>
                const aud = document.getElementById('aud');
                const pBtn = document.getElementById('pBtn');
                const sk = document.getElementById('sk');
                const msg = document.getElementById('msg');
                const spkBox = document.getElementById('spkBox');
                const script = {script_data};

                pBtn.onclick = () => {{
                    if(aud.paused) {{ aud.play(); pBtn.innerText = "⏸️ 暫停演示"; }}
                    else {{ aud.pause(); pBtn.innerText = "▶️ 繼續演示"; }}
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
                            spkBox.innerHTML = `<span class="${{s.speaker === '彥君' ? 'name yanjun-name' : 'name xiaozhen-name'}}">${{s.speaker === '彥君' ? '👨‍🏫 彥君老師' : '👩‍🔬 曉臻助教'}}</span>`;
                            msg.innerText = s.text;
                            msg.style.opacity = 1;
                            hit = true; break;
                        }}
                    }}
                    if(!hit) msg.style.opacity = 0;
                }};

                sk.oninput = () => aud.currentTime = sk.value;
                function fmt(s) {{ return Math.floor(s/60) + ":" + String(Math.floor(s%60)).padStart(2,'0'); }}
            </script>
        </body>
        </html>
        """
        components.html(full_html, height=850)
