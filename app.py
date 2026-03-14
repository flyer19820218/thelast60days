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
    /* 調整元件間距 */
    .stSelectbox, .stNumberInput { margin-bottom: 0px !important; }
    div[data-testid="column"] { display: flex; align-items: center; justify-content: center; }
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
    # --- 最上方：大標題 ---
    st.markdown("<h1 style='text-align:center; color:#1d4ed8; margin-bottom:20px;'>🚀 考前60天衝刺</h1>", unsafe_allow_html=True)

    # --- 控制列：一行三格 ---
    col1, col2, col3 = st.columns([2, 0.8, 1.2])
    unit_list = df['Day'].tolist()
    with col1:
        selected = st.selectbox("進度", unit_list, label_visibility="collapsed")
        row = df[df['Day'] == selected].iloc[0]
    with col2:
        target_page = st.number_input("頁碼", min_value=1, value=1, label_visibility="collapsed")

    # 準備檔案
    local_pdf_path = "notes.pdf"
    pdf_b64 = get_pdf_page_as_base64(local_pdf_path, target_page - 1)
    audio_path = str(row['Audio_Path']).strip().lstrip('/')
    audio_url = f"{GITHUB_RAW}{audio_path}"
    json_url = f"{GITHUB_RAW}{audio_path.replace('.mp3', '_script.json')}"

    try:
        res_json = requests.get(json_url)
        script_json_data = res_json.text if res_json.status_code == 200 else "[]"

        # --- 🔥 視覺靈魂版 HTML 🔥 ---
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{ font-family: sans-serif; margin: 0; padding: 0; background: transparent; overflow: hidden; }}
            
            /* 按鈕：定位到 Streamlit 的 col3 */
            .btn-pos {{
                position: fixed; top: -52px; right: 0; width: 30%; z-index: 9999;
                display: flex; justify-content: flex-end;
            }}
            .play-btn {{
                background: linear-gradient(135deg, #2b58db, #1d4ed8);
                color: white; padding: 8px 15px; border-radius: 50px;
                display: flex; align-items: center; gap: 8px;
                font-weight: bold; font-size: 15px; cursor: pointer;
                box-shadow: 0 4px 10px rgba(29, 78, 216, 0.3); border: none;
            }}

            .main-content {{ position: relative; width: 100%; margin-top: 10px; }}
            .pdf-view {{ width: 100%; border-radius: 8px; border: 1px solid #eee; overflow: hidden; }}
            .pdf-img {{ width: 100%; display: block; }}
            
            .seek-bar {{ width: 100%; padding: 10px 0; display: flex; align-items: center; gap: 10px; }}
            input[type=range] {{ flex: 1; accent-color: #1d4ed8; cursor: pointer; }}
            .time {{ font-size: 12px; color: #64748b; min-width: 75px; text-align: right; }}

            /* 浮動字幕泡泡 (經典框起來的感覺) */
            .bubble-container {{
                position: absolute; bottom: 80px; right: 20px;
                width: 280px; pointer-events: none;
                z-index: 1000;
            }}
            .bubble {{
                padding: 15px 20px; border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.15);
                font-size: 19px; line-height: 1.5;
                opacity: 0; transition: transform 0.3s, opacity 0.3s;
                transform: translateY(10px);
                border: 2px solid rgba(255,255,255,0.8);
            }}
            /* 彥君藍 */
            .yanjun {{ background-color: rgba(227, 242, 253, 0.95); color: #0d47a1; border-color: #bbdefb; }}
            /* 曉臻紅 (橘紅) */
            .xiaozhen {{ background-color: rgba(254, 242, 242, 0.95); color: #991b1b; border-color: #fecaca; }}
            
            .name {{ font-size: 13px; font-weight: bold; margin-bottom: 5px; opacity: 0.8; }}
        </style>
        </head>
        <body>
            <div class="btn-pos">
                <button id="playBtn" class="play-btn">▶️ 開始衝刺</button>
            </div>

            <audio id="audio" src="{audio_url}"></audio>

            <div class="main-content">
                <div class="pdf-view"><img src="data:image/png;base64,{pdf_b64}" class="pdf-img"></div>
                
                <div class="bubble-container">
                    <div id="bubble" class="bubble yanjun">
                        <div id="spk" class="name">👨‍🏫 彥君老師</div>
                        <div id="msg">準備好了嗎？</div>
                    </div>
                </div>
            </div>

            <div class="seek-bar">
                <input type="range" id="seek" value="0" step="0.1">
                <div class="time"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
            </div>

            <script>
                const audio = document.getElementById('audio');
                const btn = document.getElementById('playBtn');
                const seek = document.getElementById('seek');
                const bubble = document.getElementById('bubble');
                const script = {script_json_data};

                function fmt(s) {{
                    const m = Math.floor(s/60);
                    const sec = Math.floor(s%60);
                    return m + ":" + (sec < 10 ? "0" : "") + sec;
                }}

                btn.onclick = () => {{
                    if (audio.paused) {{ audio.play(); btn.innerText = "⏸️ 暫停"; }}
                    else {{ audio.pause(); btn.innerText = "▶️ 繼續"; }}
                }};

                audio.onloadedmetadata = () => {{
                    document.getElementById('dur').innerText = fmt(audio.duration);
                    seek.max = audio.duration;
                }};

                audio.ontimeupdate = () => {{
                    const t = audio.currentTime;
                    document.getElementById('cur').innerText = fmt(t);
                    seek.value = t;
                    let hit = false;
                    for (let s of script) {{
                        if (t >= s.start && t <= s.end) {{
                            document.getElementById('spk').innerText = (s.speaker === "彥君" ? "👨‍🏫 彥君老師" : "👩‍🔬 曉臻助教");
                            document.getElementById('msg').innerText = s.text;
                            bubble.className = "bubble " + (s.speaker === "彥君" ? "yanjun" : "xiaozhen");
                            bubble.style.opacity = 1;
                            bubble.style.transform = "translateY(0)";
                            hit = true; break;
                        }}
                    }}
                    if (!hit) {{
                        bubble.style.opacity = 0;
                        bubble.style.transform = "translateY(10px)";
                    }}
                }};
                seek.oninput = () => {{ audio.currentTime = seek.value; }};
            </script>
        </body>
        </html>
        """
        with col3: st.write("") # 佔位
        components.html(full_html, height=1000)

    except Exception as e:
        st.error(f"連線異常：{e}")
