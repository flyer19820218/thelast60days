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

    /* 頂部選單優化 */
    [data-testid="stVerticalBlock"] > div:first-child {
        background: #f1f5f9;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 0px;
    }
    
    /* 移除原生元件的多餘間距 */
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

@st.cache_data(ttl=3600)
def get_pdf_page_as_base64(local_pdf_path, page_index):
    try:
        doc = fitz.open(local_pdf_path)
        if page_index >= doc.page_count:
            doc.close()
            return "PAGE_OUT_OF_RANGE"
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0)) 
        img_data = pix.tobytes("png")
        doc.close()
        return base64.b64encode(img_data).decode('utf-8')
    except Exception as e:
        return str(e)

# ==========================================
# 2. 主介面
# ==========================================
df = load_data()

if df is not None:
    # 建立一個隱形的容器來處理頂部與 HTML 的銜接
    unit_list = df['Day'].tolist()
    
    # 這裡是關鍵：將「進度、頁碼」跟下方的「播放器」在邏輯上切分開
    c1, c2 = st.columns([3, 1])
    selected = c1.selectbox("今日進度", unit_list, label_visibility="collapsed")
    row = df[df['Day'] == selected].iloc[0]
    target_page = c2.number_input("頁碼", min_value=1, value=1, label_visibility="collapsed")

    local_pdf_path = "notes.pdf"
    pdf_b64 = get_pdf_page_as_base64(local_pdf_path, target_page - 1)

    if len(pdf_b64) > 500:
        audio_path = str(row['Audio_Path']).strip().lstrip('/')
        audio_url = f"{GITHUB_RAW}{audio_path}"
        json_url = f"{GITHUB_RAW}{audio_path.replace('.mp3', '_script.json')}"

        try:
            res_json = requests.get(json_url)
            res_json.raise_for_status()
            script_json_data = res_json.text

            # --- 🔥 極致互動介面 (播放鍵整合在頂部控制區感覺) 🔥 ---
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body {{ font-family: 'PingFang TC', sans-serif; margin: 0; padding: 0; background: white; }}
                
                .main-layout {{ width: 100%; max-width: 800px; margin: 0 auto; }}

                /* 頂部播放按鈕區 (對齊 Streamlit 的頁碼) */
                .top-control {{
                    background: #f1f5f9;
                    padding: 0 15px 15px 15px;
                    border-radius: 0 0 15px 15px;
                    display: flex;
                    justify-content: flex-end;
                    align-items: center;
                    gap: 15px;
                    margin-bottom: 10px;
                }}

                .play-capsule {{
                    background: linear-gradient(135deg, #2b58db 0%, #1d4ed8 100%);
                    color: white;
                    padding: 8px 25px;
                    border-radius: 50px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-weight: bold;
                    cursor: pointer;
                    box-shadow: 0 4px 12px rgba(29, 78, 216, 0.3);
                    user-select: none;
                }}

                .pdf-view {{
                    width: 100%;
                    background: white;
                    border: 1px solid #eee;
                    border-radius: 8px;
                    overflow: hidden;
                }}
                .pdf-img {{ width: 100%; display: block; }}

                /* 進度條拉桿 */
                .seek-container {{
                    width: 100%;
                    padding: 15px 0;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}
                input[type=range] {{
                    flex: 1;
                    accent-color: #1d4ed8;
                    cursor: pointer;
                }}
                .time-box {{ font-size: 13px; color: #475569; min-width: 80px; text-align: right; }}

                /* 字幕區塊 */
                .subtitle-box {{
                    background: #fff9f0;
                    border: 2px dashed #fed7aa;
                    border-radius: 20px;
                    padding: 20px;
                    min-height: 80px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-top: 10px;
                }}
                .bubble-text {{
                    font-size: 20px;
                    line-height: 1.6;
                    color: #1e293b;
                    text-align: center;
                    opacity: 0;
                    transition: opacity 0.2s;
                }}
                .name-tag {{ font-weight: bold; margin-bottom: 5px; font-size: 14px; color: #ea580c; }}
            </style>
            </head>
            <body>
                <div class="main-layout">
                    <div class="top-control">
                        <div id="playBtn" class="play-capsule">
                            <span id="ico">▶️</span> <span id="lbl">收聽快報</span>
                        </div>
                    </div>

                    <div class="pdf-view">
                        <img src="data:image/png;base64,{pdf_b64}" class="pdf-img">
                    </div>

                    <div class="seek-container">
                        <input type="range" id="seek" value="0" step="0.1">
                        <div class="time-box"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
                    </div>

                    <div class="subtitle-box">
                        <div id="bubble" class="bubble-text">
                            <div id="spk" class="name-tag"></div>
                            <div id="msg"></div>
                        </div>
                    </div>
                </div>

                <audio id="audio"><source src="{audio_url}" type="audio/mpeg"></audio>

                <script>
                    const audio = document.getElementById('audio');
                    const playBtn = document.getElementById('playBtn');
                    const seek = document.getElementById('seek');
                    const bubble = document.getElementById('bubble');
                    const script = {script_json_data};

                    function fmtT(s) {{
                        const m = Math.floor(s/60);
                        const sec = Math.floor(s%60);
                        return m + ":" + (sec < 10 ? "0":"") + sec;
                    }}

                    playBtn.onclick = () => {{
                        if (audio.paused) {{ 
                            audio.play(); 
                            document.getElementById('lbl').innerText="正在播放";
                            document.getElementById('ico').innerText="⏸️";
                        }} else {{ 
                            audio.pause(); 
                            document.getElementById('lbl').innerText="收聽快報";
                            document.getElementById('ico').innerText="▶️";
                        }}
                    }};

                    audio.onloadedmetadata = () => {{
                        document.getElementById('dur').innerText = fmtT(audio.duration);
                        seek.max = audio.duration;
                    }};

                    audio.ontimeupdate = () => {{
                        const t = audio.currentTime;
                        document.getElementById('cur').innerText = fmtT(t);
                        seek.value = t;

                        let found = false;
                        for (let s of script) {{
                            if (t >= s.start && t <= s.end) {{
                                document.getElementById('spk').innerText = (s.speaker === "彥君" ? "👨‍🏫 彥君老師" : "👩‍🔬 曉臻助教");
                                document.getElementById('msg').innerText = s.text;
                                bubble.style.opacity = 1;
                                found = true; break;
                            }}
                        }}
                        if (!found) bubble.style.opacity = 0;
                    }};

                    seek.oninput = () => {{ audio.currentTime = seek.value; }};
                </script>
            </body>
            </html>
            """
            components.html(html_content, height=1200)

        except Exception as e:
            st.error(f"連線異常: {e}")
