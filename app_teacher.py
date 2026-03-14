import streamlit as st
import pandas as pd
import requests
import fitz
import streamlit.components.v1 as components
import json
import base64

# ==========================================
# 1. 頁面設定 (iPad Pro 寬螢幕優化)
# ==========================================
st.set_page_config(page_title="考前60天衝刺-iPad教學版", layout="wide")

st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .stApp { background-color: #ffffff; }
    
    /* 強制字體與平滑縮放 */
    html, body, [class*="css"], p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
        -webkit-font-smoothing: antialiased;
    }
    
    /* 頂部選單容器：保持輕薄 */
    .stSelectbox, .stNumberInput { margin-bottom: 0px !important; }
    div[data-testid="column"] { display: flex; align-items: center; justify-content: center; }
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
        # iPad Pro 解析度高，使用 3.0 倍率確保清晰
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
    # 建立選單資料
    unit_list = df['Day'].tolist()
    
    # --- 第一列：選擇進度與頁碼 ---
    c_left, c_right = st.columns([3, 1])
    with c_left:
        selected_day = st.selectbox("進度", unit_list, label_visibility="collapsed")
        row = df[df['Day'] == selected_day].iloc[0]
    with c_right:
        # 教學版建議直接用 number_input 方便快速跳轉頁數
        target_page = st.number_input("頁碼", min_value=1, value=1, label_visibility="collapsed")

    # 準備資料
    pdf_b64 = get_pdf_page_as_base64("notes.pdf", target_page - 1)
    audio_path = str(row['Audio_Path']).strip().lstrip('/')
    audio_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path}"
    json_url = audio_url.replace('.mp3', '_script.json')

    try:
        res_json = requests.get(json_url)
        script_data_str = res_json.text if res_json.status_code == 200 else "[]"

        # --- 🔥 旗艦 iPad Pro 16:9 教學介面 🔥 ---
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{ font-family: sans-serif; margin: 0; padding: 0; background: white; }}
            
            /* 1. 標題與按鈕：橫向一體化 (復刻你最愛的版本) */
            .header-row {{
                display: flex; align-items: center; justify-content: space-between;
                padding: 10px 0; border-bottom: 1px solid #f0f0f0; margin-bottom: 15px;
            }}
            .title {{ color: #1d4ed8; font-size: 36px; font-weight: bold; margin: 0; }}
            .play-capsule {{
                background: linear-gradient(135deg, #2b58db, #1d4ed8);
                color: white; padding: 10px 25px; border-radius: 50px;
                display: flex; align-items: center; gap: 10px;
                font-weight: bold; font-size: 18px; cursor: pointer;
                box-shadow: 0 4px 15px rgba(29, 78, 216, 0.4); border: none;
            }}

            /* 2. 主內容：16:9 比例優化 */
            .main-content {{ width: 100%; max-width: 1100px; margin: 0 auto; }}
            .pdf-frame {{ 
                width: 100%; background: white; border-radius: 15px; 
                box-shadow: 0 8px 30px rgba(0,0,0,0.08); overflow: hidden; 
                border: 1px solid #eee;
            }}
            .pdf-img {{ width: 100%; display: block; }}
            
            /* 3. 進度條：iPad 觸控優化 */
            .seek-bar-row {{ width: 100%; padding: 20px 0; display: flex; align-items: center; gap: 15px; }}
            input[type=range] {{ flex: 1; accent-color: #1d4ed8; cursor: pointer; height: 10px; }}
            .time-display {{ font-size: 14px; color: #64748b; min-width: 100px; text-align: right; }}

            /* 4. 字幕：左右分立、不擋講義 (靈魂回歸) */
            .subtitle-stage {{
                width: 100%; min-height: 140px; display: flex; flex-direction: column; padding: 10px 0;
            }}
            .bubble {{
                max-width: 70%; padding: 18px 24px; border-radius: 20px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                font-size: 24px; line-height: 1.6; opacity: 0;
                transition: all 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.28);
                position: relative;
            }}
            .yanjun {{
                align-self: flex-start;
                background-color: #e3f2fd; color: #0d47a1;
                border: 2px solid #bbdefb; border-bottom-left-radius: 2px;
            }}
            .xiaozhen {{
                align-self: flex-end;
                background-color: #fef2f2; color: #991b1b;
                border: 2px solid #fecaca; border-bottom-right-radius: 2px;
            }}
            .speaker-name {{ font-size: 14px; font-weight: bold; margin-bottom: 6px; opacity: 0.8; }}
        </style>
        </head>
        <body>
            <div class="main-content">
                <div class="header-row">
                    <div class="title">🚀 考前60天衝刺</div>
                    <button id="pBtn" class="play-capsule">▶️ 收聽快報</button>
                </div>

                <audio id="aud" src="{audio_url}"></audio>

                <div class="pdf-frame">
                    <img src="data:image/png;base64,{pdf_b64}" class="pdf-img">
                </div>

                <div class="seek-bar-row">
                    <input type="range" id="sk" value="0" step="0.1">
                    <div class="time-display"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
                </div>

                <div class="subtitle-stage">
                    <div id="bubble" class="bubble yanjun">
                        <div id="spk" class="speaker-name"></div>
                        <div id="msg">準備好了嗎？</div>
                    </div>
                </div>
            </div>

            <script>
                const aud = document.getElementById('aud');
                const pBtn = document.getElementById('pBtn');
                const sk = document.getElementById('sk');
                const bubble = document.getElementById('bubble');
                const spk = document.getElementById('spk');
                const msg = document.getElementById('msg');
                const script = {script_data_str};

                function fmt(s) {{
                    const m = Math.floor(s/60);
                    const sec = Math.floor(s%60);
                    return m + ":" + (sec < 10 ? "0" : "") + sec;
                }}

                pBtn.onclick = () => {{
                    if (aud.paused) {{
                        aud.play(); pBtn.innerText = "⏸️ 暫停衝刺";
                    }} else {{
                        aud.pause(); pBtn.innerText = "▶️ 繼續衝刺";
                    }}
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
                    for(let i=0; i<script.length; i++) {{
                        const s = script[i];
                        if(t >= s.start && t <= s.end) {{
                            spk.innerText = (s.speaker === '彥君' ? '👨‍🏫 彥君老師' : '👩‍🔬 曉臻助教');
                            msg.innerText = s.text;
                            bubble.className = 'bubble ' + (s.speaker === '彥君' ? 'yanjun' : 'xiaozhen');
                            bubble.style.opacity = 1;
                            hit = true; break;
                        }}
                    }}
                    if(!hit) bubble.style.opacity = 0;
                }};
                sk.oninput = () => aud.currentTime = sk.value;
            </script>
        </body>
        </html>
        """
        components.html(full_html, height=1350)

    except Exception as e:
        st.error(f"⚠️ 資料解析出錯: {e}")
