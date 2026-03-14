import streamlit as st
import pandas as pd
import requests
import fitz
import streamlit.components.v1 as components
import json
import base64

# ==========================================
# 1. 頁面設定 (iPad Pro 究極教學版)
# ==========================================
st.set_page_config(page_title="會考自然-旗艦護法版", layout="wide")

st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .stApp { background-color: #ffffff; }
    
    html, body, [class*="css"], p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
    }
    
    .stSelectbox, .stNumberInput { margin-bottom: 0px !important; }
    div[data-testid="column"] { display: flex; align-items: center; justify-content: center; }
    </style>
    """, unsafe_allow_html=True)

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
        pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0)) 
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
    unit_list = df['Day'].tolist()
    c_left, c_right = st.columns([3, 1])
    with c_left:
        selected_day = st.selectbox("進度", unit_list, label_visibility="collapsed")
        row = df[df['Day'] == selected_day].iloc[0]
    with c_right:
        target_page = st.number_input("頁碼", min_value=1, value=1, label_visibility="collapsed")

    pdf_b64 = get_pdf_page_as_base64("notes.pdf", target_page - 1)
    audio_path = str(row['Audio_Path']).strip().lstrip('/')
    audio_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path}"
    json_url = audio_url.replace('.mp3', '_script.json')

    try:
        res_json = requests.get(json_url)
        script_data = res_json.text if res_json.status_code == 200 else "[]"

        # --- 🔥 究極合體 HTML 🔥 ---
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{ font-family: sans-serif; margin: 0; padding: 0; background: white; overflow: hidden; }}
            
            /* 1. 頂部列 */
            .header-bar {{
                display: flex; align-items: center; justify-content: space-between;
                padding: 10px 20px; border-bottom: 1px solid #f0f0f0;
            }}
            .title {{ color: #1d4ed8; font-size: 34px; font-weight: bold; margin: 0; }}
            .play-btn {{
                background: linear-gradient(135deg, #2b58db, #1d4ed8);
                color: white; padding: 10px 25px; border-radius: 50px;
                display: flex; align-items: center; gap: 10px;
                font-weight: bold; font-size: 18px; cursor: pointer;
                box-shadow: 0 4px 15px rgba(29, 78, 216, 0.4); border: none;
            }}

            /* 2. 主舞台佈局 */
            .main-stage {{
                display: flex; align-items: flex-start; justify-content: center;
                width: 100%; height: 85vh; padding-top: 15px; position: relative;
            }}
            
            /* 講義核心 */
            .center-column {{
                flex: 0 0 auto; width: 65%;
                display: flex; flex-direction: column; align-items: center;
            }}
            
            .pdf-view {{ 
                width: 100%; background: white; border-radius: 12px 12px 0 0; 
                box-shadow: 0 10px 40px rgba(0,0,0,0.1); overflow: hidden;
                border: 1px solid #eee; border-bottom: none;
            }}
            .pdf-img {{ width: 100%; display: block; }}

            /* 緊連 PDF 的進度條區 */
            .progress-panel {{
                width: 100%; background: #f8fafc; padding: 10px 15px;
                border: 1px solid #eee; border-radius: 0 0 12px 12px;
                display: flex; align-items: center; gap: 15px; box-sizing: border-box;
            }}
            input[type=range] {{ flex: 1; accent-color: #1d4ed8; cursor: pointer; height: 8px; }}
            .time-box {{ font-size: 13px; color: #64748b; min-width: 85px; text-align: right; font-family: monospace; }}

            /* 3. 左右護法 (位置微調) */
            .side-box {{
                flex: 1; height: 100%; display: flex; flex-direction: column;
                justify-content: flex-start; padding: 60px 20px 0 20px; box-sizing: border-box;
            }}

            .bubble {{
                padding: 20px; border-radius: 20px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                font-size: 22px; line-height: 1.5; opacity: 0;
                transition: all 0.3s ease; transform: translateY(10px);
            }}
            .yanjun {{ background-color: #e3f2fd; color: #0d47a1; border: 2px solid #bbdefb; }}
            .xiaozhen {{ background-color: #fef2f2; color: #991b1b; border: 2px solid #fecaca; }}
            .name {{ font-size: 14px; font-weight: bold; margin-bottom: 8px; }}
        </style>
        </head>
        <body>
            <div class="header-bar">
                <div class="title">🚀 考前60天衝刺</div>
                <button id="pBtn" class="play-btn">▶️ 收聽快報</button>
            </div>

            <audio id="aud" src="{audio_url}"></audio>

            <div class="main-stage">
                <div class="side-box">
                    <div id="yjB" class="bubble yanjun">
                        <div class="name">👨‍🏫 彥君老師</div>
                        <div id="yjT"></div>
                    </div>
                </div>

                <div class="center-column">
                    <div class="pdf-view">
                        <img src="data:image/png;base64,{pdf_b64}" class="pdf-img">
                    </div>
                    <div class="progress-panel">
                        <input type="range" id="sk" value="0" step="0.1">
                        <div class="time-box"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
                    </div>
                </div>

                <div class="side-box">
                    <div id="xzB" class="bubble xiaozhen">
                        <div class="name">👩‍🔬 曉臻助教</div>
                        <div id="xzT"></div>
                    </div>
                </div>
            </div>

            <script>
                const aud = document.getElementById('aud');
                const pBtn = document.getElementById('pBtn');
                const sk = document.getElementById('sk');
                const yjB = document.getElementById('yjB'), xzB = document.getElementById('xzB');
                const yjT = document.getElementById('yjT'), xzT = document.getElementById('xzT');
                const script = {script_data};

                pBtn.onclick = () => {{
                    if(aud.paused) {{ aud.play(); pBtn.innerText = "⏸️ 暫停衝刺"; }}
                    else {{ aud.pause(); pBtn.innerText = "▶️ 繼續衝刺"; }}
                }};

                aud.onloadedmetadata = () => {{
                    document.getElementById('dur').innerText = fmt(aud.duration);
                    sk.max = aud.duration;
                }};

                aud.ontimeupdate = () => {{
                    const t = aud.currentTime;
                    document.getElementById('cur').innerText = fmt(t);
                    sk.value = t;
                    let yH = false, xH = false;
                    for(let i=0; i<script.length; i++) {{
                        const s = script[i];
                        if(t >= s.start && t <= s.end) {{
                            if(s.speaker === '彥君') {{ yjT.innerText = s.text; yjB.style.opacity = 1; yjB.style.transform = "translateY(0)"; yH = true; }}
                            else {{ xzT.innerText = s.text; xzB.style.opacity = 1; xzB.style.transform = "translateY(0)"; xH = true; }}
                        }}
                    }}
                    if(!yH) {{ yjB.style.opacity = 0; yjB.style.transform = "translateY(10px)"; }}
                    if(!xH) {{ xzB.style.opacity = 0; xzB.style.transform = "translateY(10px)"; }}
                }};

                sk.oninput = () => aud.currentTime = sk.value;
                function fmt(s) {{ return Math.floor(s/60) + ":" + String(Math.floor(s%60)).padStart(2,'0'); }}
            </script>
        </body>
        </html>
        """
        components.html(full_html, height=1100)

    except Exception as e:
        st.error(f"連線異常: {e}")
