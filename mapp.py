import streamlit as st
import pandas as pd
import requests
import fitz  # PyMuPDF
import streamlit.components.v1 as components
import json
import base64

# ==========================================
# 1. 頁面基礎設定
# ==========================================
st.set_page_config(page_title="國中自然60天逆襲", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: #ffffff; }
    html, body, [class*="css"], p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
    }
    /* 讓選單列變細，不佔空間 */
    .stSelectbox, .stNumberInput { margin-bottom: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

USER = "flyer19820218"
REPO = "thelast60days"
GITHUB_RAW = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/"

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
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0)) 
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
    # 頂部控制列：純數據選擇
    c1, c2 = st.columns([3, 1])
    unit_list = df['Day'].tolist()
    with c1:
        selected = st.selectbox("進度", unit_list, label_visibility="collapsed")
        row = df[df['Day'] == selected].iloc[0]
    with c2:
        target_page = st.number_input("頁碼", min_value=1, value=1, label_visibility="collapsed")

    # 準備檔案路徑
    local_pdf_path = "notes.pdf"
    pdf_b64 = get_pdf_page_as_base64(local_pdf_path, target_page - 1)
    audio_path = str(row['Audio_Path']).strip().lstrip('/')
    audio_url = f"{GITHUB_RAW}{audio_path}"
    json_url = f"{GITHUB_RAW}{audio_path.replace('.mp3', '_script.json')}"

    try:
        res_json = requests.get(json_url)
        script_json_data = res_json.text if res_json.status_code == 200 else "[]"

        # --- 🔥 旗艦大整合 HTML 🔥 ---
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{ font-family: sans-serif; margin: 0; padding: 0; background: white; }}
            
            /* 1. 標題與播放鍵並排列 */
            .header-container {{
                display: flex; align-items: center; justify-content: space-between;
                padding: 10px 0; margin-bottom: 5px;
            }}
            .title-text {{
                color: #1d4ed8; font-size: 32px; font-weight: bold; margin: 0;
                display: flex; align-items: center; gap: 10px;
            }}
            .play-capsule {{
                background: linear-gradient(135deg, #2b58db, #1d4ed8);
                color: white; padding: 8px 22px; border-radius: 50px;
                display: flex; align-items: center; gap: 10px;
                font-weight: bold; font-size: 16px; cursor: pointer;
                box-shadow: 0 4px 12px rgba(29, 78, 216, 0.4); border: none;
                transition: transform 0.2s;
            }}
            .play-capsule:active {{ transform: scale(0.95); }}

            /* 2. PDF 區域 */
            .pdf-view {{ width: 100%; border-radius: 12px; border: 1px solid #eee; overflow: hidden; }}
            .pdf-img {{ width: 100%; display: block; }}
            
            /* 3. 進度條 */
            .seek-area {{ width: 100%; padding: 15px 0; display: flex; align-items: center; gap: 10px; }}
            input[type=range] {{ flex: 1; accent-color: #1d4ed8; cursor: pointer; }}
            .time-label {{ font-size: 13px; color: #64748b; min-width: 85px; text-align: right; }}

            /* 4. 分離式左右字幕泡泡 */
            .subtitle-stage {{
                width: 100%; min-height: 110px; display: flex; flex-direction: column; padding-top: 5px;
            }}
            .bubble {{
                max-width: 75%; padding: 14px 18px; border-radius: 18px;
                box-shadow: 0 6px 20px rgba(0,0,0,0.1);
                font-size: 20px; line-height: 1.5; opacity: 0;
                transition: all 0.3s ease;
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
            .speaker-name {{ font-size: 12px; font-weight: bold; margin-bottom: 4px; opacity: 0.8; }}
        </style>
        </head>
        <body>
            <div class="header-container">
                <div class="title-text">🚀 考前60天衝刺</div>
                <button id="mainPlayBtn" class="play-capsule">▶️ 收聽快報</button>
            </div>

            <audio id="coreAudio" src="{audio_url}"></audio>

            <div class="pdf-view">
                <img src="data:image/png;base64,{pdf_b64}" class="pdf-img">
            </div>
            
            <div class="seek-area">
                <input type="range" id="seekSlider" value="0" step="0.1">
                <div class="time-label"><span id="curTime">0:00</span> / <span id="durTime">0:00</span></div>
            </div>

            <div class="subtitle-stage">
                <div id="bubbleWrap" class="bubble yanjun">
                    <div id="spkLabel" class="speaker-name"></div>
                    <div id="msgText"></div>
                </div>
            </div>

            <script>
                const audio = document.getElementById('coreAudio');
                const btn = document.getElementById('mainPlayBtn');
                const seek = document.getElementById('seekSlider');
                const bubble = document.getElementById('bubbleWrap');
                const script = {script_json_data};

                function fmt(s) {{
                    const m = Math.floor(s/60);
                    const sec = Math.floor(s%60);
                    return m + ":" + (sec < 10 ? "0" : "") + sec;
                }}

                btn.onclick = () => {{
                    if (audio.paused) {{
                        audio.play();
                        btn.innerText = "⏸️ 暫停衝刺";
                    }} else {{
                        audio.pause();
                        btn.innerText = "▶️ 繼續衝刺";
                    }}
                }};

                audio.onloadedmetadata = () => {{
                    document.getElementById('durTime').innerText = fmt(audio.duration);
                    seek.max = audio.duration;
                }};

                audio.ontimeupdate = () => {{
                    const t = audio.currentTime;
                    document.getElementById('curTime').innerText = fmt(t);
                    seek.value = t;
                    let hit = false;
                    for (let s of script) {{
                        if (t >= s.start && t <= s.end) {{
                            document.getElementById('spkLabel').innerText = (s.speaker === "彥君" ? "👨‍🏫 彥君老師" : "👩‍🔬 曉臻助教");
                            document.getElementById('msgText').innerText = s.text;
                            bubble.className = "bubble " + (s.speaker === "彥君" ? "yanjun" : "xiaozhen");
                            bubble.style.opacity = 1;
                            hit = true; break;
                        }}
                    }}
                    if (!hit) bubble.style.opacity = 0;
                }};
                seek.oninput = () => {{ audio.currentTime = seek.value; }};
            </script>
        </body>
        </html>
        """
        # 渲染：這次直接一步到位
        components.html(full_html, height=1250)

    except Exception as e:
        st.error(f"連線異常：{e}")
