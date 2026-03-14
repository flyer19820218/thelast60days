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
    /* 讓 Streamlit 的 columns 內部垂直居中 */
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
    # --- 最上方：火箭大標題 ---
    st.markdown("<h1 style='text-align:center; color:#1d4ed8; margin-top:0;'>🚀 考前60天衝刺</h1>", unsafe_allow_html=True)

    # --- 控制列：一行三格 ---
    # 我們讓按鈕乖乖在第三格，不玩定位了
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

        # --- 🔥 旗艦完整版 HTML (按鈕在右邊，字幕會浮動) 🔥 ---
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{ font-family: sans-serif; margin: 0; padding: 0; background: white; }}
            
            /* 第三格內的按鈕樣式 */
            .btn-container {{ display: flex; justify-content: flex-end; padding-bottom: 10px; }}
            .play-btn {{
                background: linear-gradient(135deg, #2b58db, #1d4ed8);
                color: white; padding: 8px 15px; border-radius: 50px;
                display: flex; align-items: center; gap: 8px;
                font-weight: bold; font-size: 15px; cursor: pointer;
                box-shadow: 0 4px 10px rgba(29, 78, 216, 0.3); border: none;
                user-select: none;
            }}

            .main-content {{ position: relative; width: 100%; }}
            .pdf-view {{ width: 100%; border-radius: 8px; border: 1px solid #eee; overflow: hidden; }}
            .pdf-img {{ width: 100%; display: block; }}
            
            .seek-bar-row {{ width: 100%; padding: 12px 0; display: flex; align-items: center; gap: 10px; }}
            input[type=range] {{ flex: 1; accent-color: #1d4ed8; cursor: pointer; }}
            .time-txt {{ font-size: 12px; color: #64748b; min-width: 80px; text-align: right; }}

            /* 浮動字幕泡泡 */
            .bubble-stage {{
                position: absolute; bottom: 60px; right: 20px;
                width: 300px; pointer-events: none; z-index: 999;
            }}
            .bubble {{
                padding: 18px 25px; border-radius: 20px;
                box-shadow: 0 12px 40px rgba(0,0,0,0.18);
                font-size: 20px; line-height: 1.6;
                opacity: 0; transition: all 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.28);
                transform: translateY(20px);
                border: 2px solid rgba(255,255,255,0.9);
            }}
            .yanjun {{ background-color: rgba(227, 242, 253, 0.98); color: #0d47a1; border-color: #bbdefb; }}
            .xiaozhen {{ background-color: rgba(254, 242, 242, 0.98); color: #991b1b; border-color: #fecaca; }}
            .name-label {{ font-size: 13px; font-weight: bold; margin-bottom: 6px; opacity: 0.8; }}
        </style>
        </head>
        <body>
            <div class="btn-container">
                <div id="playBtn" class="play-btn">
                    <span id="ico">▶️</span> <span id="lbl">收聽快報</span>
                </div>
            </div>

            <audio id="audio" src="{audio_url}"></audio>

            <div class="main-content">
                <div class="pdf-view"><img src="data:image/png;base64,{pdf_b64}" class="pdf-img"></div>
                
                <div class="bubble-stage">
                    <div id="bubble" class="bubble yanjun">
                        <div id="spk" class="name-label">👨‍🏫 彥君老師</div>
                        <div id="msg">開始今日衝刺！</div>
                    </div>
                </div>
            </div>

            <div class="seek-bar-row">
                <input type="range" id="seek" value="0" step="0.1">
                <div class="time-txt"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
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
                    if (audio.paused) {{
                        audio.play();
                        document.getElementById('lbl').innerText = "衝刺中";
                        document.getElementById('ico').innerText = "⏸️";
                    }} else {{
                        audio.pause();
                        document.getElementById('lbl').innerText = "繼續衝刺";
                        document.getElementById('ico').innerText = "▶️";
                    }}
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
                        bubble.style.transform = "translateY(20px)";
                    }}
                }};
                seek.oninput = () => {{ audio.currentTime = seek.value; }};
            </script>
        </body>
        </html>
        """
        # 渲染：這一次高度設定 1200 確保組件完全顯示
        with col3:
            st.empty() # 雖然我們在 HTML 裡畫按鈕，但還是留個空位給 Streamlit 佈局
        components.html(full_html, height=1200)

    except Exception as e:
        st.error(f"連線異常：{e}")
