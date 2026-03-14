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
    /* 加強按鈕樣式 */
    div.stButton > button {
        background: linear-gradient(135deg, #2b58db, #1d4ed8);
        color: white; border-radius: 50px; border: none;
        font-weight: bold; width: 100%; height: 45px;
        box-shadow: 0 4px 10px rgba(29, 78, 216, 0.3);
    }
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
    # --- 第一列：大標題 + 原生播放按鈕 ---
    t_col1, t_col2 = st.columns([3, 1])
    with t_col1:
        st.markdown("<h2 style='margin:0; color:#1d4ed8;'>🚀 考前60天衝刺</h2>", unsafe_allow_html=True)
    
    # 建立一個 Session State 來控制播放
    if 'play_trigger' not in st.session_state:
        st.session_state.play_trigger = False

    with t_col2:
        if st.button("▶️ 開始衝刺"):
            st.session_state.play_trigger = not st.session_state.play_trigger

    # --- 第二列：進度選單 + 頁碼 ---
    m_col1, m_col2 = st.columns([3, 1])
    unit_list = df['Day'].tolist()
    with m_col1:
        selected = st.selectbox("進度", unit_list, label_visibility="collapsed")
        row = df[df['Day'] == selected].iloc[0]
    with m_col2:
        target_page = st.number_input("頁碼", min_value=1, value=1, label_visibility="collapsed")

    # 準備講義與檔案
    local_pdf_path = "notes.pdf"
    pdf_b64 = get_pdf_page_as_base64(local_pdf_path, target_page - 1)
    audio_path = str(row['Audio_Path']).strip().lstrip('/')
    audio_url = f"{GITHUB_RAW}{audio_path}"
    json_url = f"{GITHUB_RAW}{audio_path.replace('.mp3', '_script.json')}"

    try:
        res_json = requests.get(json_url)
        script_json_data = res_json.text if res_json.status_code == 200 else "[]"

        # --- 🔥 核心連動 HTML 🔥 ---
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{ font-family: sans-serif; margin: 0; padding: 0; background: white; }}
            .pdf-view {{ width: 100%; border-radius: 8px; border: 1px solid #eee; overflow: hidden; margin-top: 10px; }}
            .pdf-img {{ width: 100%; display: block; }}
            .seek-container {{ width: 100%; padding: 10px 0; display: flex; align-items: center; gap: 10px; }}
            input[type=range] {{ flex: 1; accent-color: #1d4ed8; cursor: pointer; }}
            .time-box {{ font-size: 12px; color: #64748b; min-width: 80px; text-align: right; }}
            .bubble-box {{ background: #fff9f0; border: 2px dashed #fed7aa; border-radius: 15px; padding: 15px; min-height: 60px; display: flex; flex-direction: column; justify-content: center; align-items: center; }}
            .text {{ font-size: 19px; color: #1e293b; text-align: center; opacity: 0; transition: opacity 0.2s; }}
            .tag {{ font-weight: bold; font-size: 13px; color: #ea580c; margin-bottom: 3px; }}
        </style>
        </head>
        <body>
            <audio id="audio" src="{audio_url}"></audio>
            <div class="pdf-view"><img src="data:image/png;base64,{pdf_b64}" class="pdf-img"></div>
            <div class="seek-container">
                <input type="range" id="seek" value="0" step="0.1">
                <div class="time-box"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
            </div>
            <div class="bubble-box">
                <div id="bubble" class="text">
                    <div id="spk" class="tag"></div>
                    <div id="msg"></div>
                </div>
            </div>

            <script>
                const audio = document.getElementById('audio');
                const seek = document.getElementById('seek');
                const bubble = document.getElementById('bubble');
                const script = {script_json_data};

                // 💡 監聽來自 Python 的播放指令
                window.addEventListener('message', function(event) {{
                    if (audio.paused) audio.play(); else audio.pause();
                }});

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
        
        # 渲染組件
        components.html(full_html, height=1000)

    except Exception as e:
        st.error(f"連線異常：{e}")

# 💡 這裡就是按鈕與 HTML 溝通的秘密通道
if st.session_state.play_trigger:
    components.html("<script>window.parent.postMessage('play', '*');</script>", height=0)
