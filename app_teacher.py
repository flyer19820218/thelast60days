import streamlit as st
import pandas as pd
import requests
import fitz
import streamlit.components.v1 as components
import base64
import time

# ==========================================
# 1. 頁面設定
# ==========================================
st.set_page_config(page_title="會考自然-考前60天衝刺", layout="wide")

st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .stApp { background: #ffffff; }
    html, body, [class*="css"], p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
    }
    .stSelectbox {
        margin-bottom: -79px !important; 
        position: relative;
        z-index: 101;
        width: 18% !important;
        margin-left: 450px !important; 
        top: -2px; 
    }
    .stSelectbox div[data-baseweb="select"] {
        font-size: 24px !important;
        font-weight: bold !important;
        height: 45px !important;
        line-height: 45px !important;
        display: flex !important;
        align-items: center !important;
    }
    .stSelectbox label { display: none !important; } 
</style>
""", unsafe_allow_html=True)

def load_data_raw():
    url = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
    try:
        r = requests.get(f"{url}&nocache={time.time()}")
        from io import StringIO
        return pd.read_csv(StringIO(r.text))
    except:
        return None

def get_pdf_page_64(page_idx):
    try:
        doc = fitz.open("notes.pdf")
        page = doc.load_page(page_idx)
        pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0)) 
        return base64.b64encode(pix.tobytes("png")).decode('utf-8')
    except:
        return ""

# ==========================================
# 2. 佈局實作
# ==========================================
df = load_data_raw()

if df is not None:
    if 'page_idx' not in st.session_state:
        st.session_state.page_idx = 0

    try:
        # 🌟 路徑校準：強制去 audio/ 資料夾找檔案
        current_page_num = st.session_state.page_idx + 1
        audio_filename = f"p{current_page_num}.mp3"
        json_filename = f"p{current_page_num}_script.json"
        
        ts = int(time.time() * 1000)
        # 這裡路徑加上了 /audio/
        base_url = "https://raw.githubusercontent.com/flyer19820218/thelast60days/main/audio"
        
        audio_url = f"{base_url}/{audio_filename}?v={ts}"
        json_url = f"{base_url}/{json_filename}?v={ts}"
        
        pdf_b64 = get_pdf_page_64(st.session_state.page_idx)
        res_json = requests.get(json_url)
        script_data = res_json.text if res_json.status_code == 200 else "[]"

        page_labels = [f"第 {i+1} 頁" for i in range(len(df))]
        selected_label = st.selectbox("", page_labels, index=st.session_state.page_idx)
        
        if page_labels.index(selected_label) != st.session_state.page_idx:
            st.session_state.page_idx = page_labels.index(selected_label)
            st.rerun()

        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{ font-family: sans-serif; margin: 0; padding: 0; background: white; }}
            .nav-bar {{ 
                display: flex; align-items: center; justify-content: space-between; 
                padding: 10px 40px; background: #f8fafc; border-bottom: 5px solid #1e40af;
                height: 95px; box-sizing: border-box;
            }}
            .nav-left {{ display: flex; align-items: center; }}
            .nav-title {{ color: #1e40af; font-size: 38px; font-weight: 950; white-space: nowrap; }}
            .spacer {{ width: 35%; }} 
            .play-btn {{ 
                background: #1e40af; color: white; padding: 12px 40px; border-radius: 50px; 
                border: none; font-size: 26px; font-weight: bold; cursor: pointer;
                box-shadow: 0 4px 15px rgba(30,64,175,0.3);
            }}
            .pdf-view {{ width: 100%; }}
            .pdf-img {{ width: 100%; display: block; }}
            .seek-panel {{ width: 100%; background: #f1f5f9; padding: 25px 40px; display: flex; align-items: center; gap: 20px; box-sizing: border-box; }}
            input[type=range] {{ flex: 1; accent-color: #1e40af; height: 22px; }}
            .time-box {{ font-size: 24px; color: #1e293b; min-width: 140px; text-align: right; font-family: monospace; font-weight: bold; }}
            .subtitle-stage {{ width: 100%; min-height: 240px; display: flex; flex-direction: column; padding: 40px; box-sizing: border-box; }}
            .bubble {{ max-width: 85%; padding: 30px; border-radius: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); font-size: 36px; line-height: 1.5; opacity: 0; transition: 0.2s ease; }}
            .yj {{ align-self: flex-start; background: #e0f2fe; color: #0369a1; border: 2px solid #bae6fd; }}
            .xz {{ align-self: flex-end; background: #fff1f2; color: #be123c; border: 2px solid #fecdd3; }}
        </style>
        </head>
        <body>
            <div class="nav-bar">
                <div class="nav-left">
                    <span class="nav-title">🚀 考前60天衝刺</span>
                </div>
                <div class="spacer"></div>
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
        components.html(full_html, height=2300, scrolling=True)

    except Exception as e:
        st.error(f"系統異常：{e}")
