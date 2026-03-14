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
    /* 移除原生元件多餘間距 */
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
    # 頂部：火箭大標題
    st.markdown("<h1 style='text-align:center; color:#1d4ed8; margin-bottom:10px;'>🚀 考前60天衝刺</h1>", unsafe_allow_html=True)

    # 控制列：單純放選單跟頁碼
    c1, c2 = st.columns([3, 1])
    unit_list = df['Day'].tolist()
    with c1:
        selected = st.selectbox("進度", unit_list, label_visibility="collapsed")
        row = df[df['Day'] == selected].iloc[0]
    with c2:
        target_page = st.number_input("頁碼", min_value=1, value=1, label_visibility="collapsed")

    # 準備資料
    local_pdf_path = "notes.pdf"
    pdf_b64 = get_pdf_page_as_base64(local_pdf_path, target_page - 1)
    audio_path = str(row['Audio_Path']).strip().lstrip('/')
    audio_url = f"{GITHUB_RAW}{audio_path}"
    json_url = f"{GITHUB_RAW}{audio_path.replace('.mp3', '_script.json')}"

    try:
        res_json = requests.get(json_url)
        script_json_data = res_json.text if res_json.status_code == 200 else "[]"

        # --- 🔥 終極大一統：把所有東西都包在一個 HTML 裡 🔥 ---
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{ font-family: sans-serif; margin: 0; padding: 0; background: white; }}
            
            /* 播放列：跟 PDF 緊連在一起 */
            .top-bar {{
                display: flex; justify-content: flex-end; padding: 10px 0;
            }}
            .play-btn {{
                background: linear-gradient(135deg, #2b58db, #1d4ed8);
                color: white; padding: 8px 18px; border-radius: 50px;
                display: flex; align-items: center; gap: 8px;
                font-weight: bold; font-size: 15px; cursor: pointer;
                box-shadow: 0 4px 10px rgba(29, 78, 216, 0.3); border: none;
            }}

            .pdf-view {{ width: 100%; border-radius: 8px; border: 1px solid #eee; overflow: hidden; }}
            .pdf-img {{ width: 100%; display: block; }}
            
            .seek-row {{ width: 100%; padding: 12px 0; display: flex; align-items: center; gap: 10px; }}
            input[type=range] {{ flex: 1; accent-color: #1d4ed8; cursor: pointer; }}
            .time-txt {{ font-size: 12px; color: #64748b; min-width: 80px; text-align: right; }}

            /* 字幕舞台 */
            .chat-stage {{ width: 100%; min-height: 120px; display: flex; flex-direction: column; padding: 10px 0; }}
            .bubble {{
                max-width: 80%; padding: 15px 20px; border-radius: 18px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08); font-size: 19px; line-height: 1.5;
                opacity: 0; transition: all 0.3s ease;
            }}
            .yanjun {{ align-self: flex-start; background: #e3f2fd; color: #0d47a1; border: 2px solid #bbdefb; border-bottom-left-radius: 2px; }}
            .xiaozhen {{ align-self: flex-end; background: #fef2f2; color: #991b1b; border: 2px solid #fecaca; border-bottom-right-radius: 2px; }}
            .name {{ font-size: 12px; font-weight: bold; margin-bottom: 4px; opacity: 0.8; }}
        </style>
        </head>
        <body>
            <div class="top-bar">
                <button id="playBtn" class="play-btn">▶️ 開始衝刺</button>
            </div>

            <audio id="audio" src="{audio_url}"></audio>

            <div class="pdf-view"><img src="data:image/png;base64,{pdf_b64}" class="pdf-img"></div>
            
            <div class="seek-row">
                <input type="range" id="seek" value="0" step="0.1">
                <div class="time-txt"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
            </div>

            <div class="chat-stage">
                <div id="bubble" class="bubble yanjun">
                    <div id="spk" class="name"></div>
                    <div id="msg"></div>
                </div>
            </div>

            <script>
                const audio = document.getElementById('audio');
                const btn = document.getElementById('playBtn');
                const seek = document.getElementById('seek');
                const bubble = document.getElementById('bubble');
                const script = {script_json_data};

                btn.onclick = () => {{
                    if (audio.paused) {{
                        audio.play(); btn.innerText = "⏸️ 暫停";
                    }} else {{
                        audio.pause(); btn.innerText = "▶️ 繼續";
                    }}
                }};

                function fmt(s) {{
                    const m = Math.floor(s/60);
                    const sec = Math.floor(s%60);
                    return m + ":" + (sec < 10 ? "0" : "") + sec;
                }}

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
        components.html(full_html, height=1300)

    except Exception as e:
        st.error(f"⚠️ 載入錯誤：{e}")
