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

    /* 控制面板外框：做成淺色背景長條 */
    .control-panel {
        background: #f1f5f9;
        padding: 10px 15px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }
    
    /* 讓 Streamlit 的 columns 內部垂直居中 */
    [data-testid="column"] {
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* 移除輸入框多餘的空白 */
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
# 2. 主控制面板 (一行三格)
# ==========================================
df = load_data()

if df is not None:
    # 建立橫向三格
    col1, col2, col3 = st.columns([2, 0.8, 1.2])
    
    unit_list = df['Day'].tolist()
    with col1:
        selected = st.selectbox("進度", unit_list, label_visibility="collapsed")
        row = df[df['Day'] == selected].iloc[0]
    
    with col2:
        target_page = st.number_input("頁碼", min_value=1, value=1, label_visibility="collapsed")

    # 準備 PDF 圖片
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

            # --- 🔥 HTML/JS 輕量化控制按鈕 (放在第三格) 🔥 ---
            btn_html = f"""
            <div id="playBtn" style="
                background: linear-gradient(135deg, #2b58db 0%, #1d4ed8 100%);
                color: white;
                padding: 8px 15px;
                border-radius: 50px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                font-family: sans-serif;
                font-weight: bold;
                font-size: 15px;
                cursor: pointer;
                box-shadow: 0 4px 10px rgba(29, 78, 216, 0.3);
                user-select: none;
                white-space: nowrap;
            ">
                <span id="ico">▶️</span> <span id="lbl">收聽快報</span>
            </div>
            <audio id="audio"><source src="{audio_url}" type="audio/mpeg"></audio>
            
            <script>
                const audio = document.getElementById('audio');
                const btn = document.getElementById('playBtn');
                
                // 這裡我們需要一個機制讓 HTML 跟 Streamlit 的進度條溝通，但因為是三格並行，
                // 我們先把播放控制寫在這裡，進度條放在 PDF 下方。
                btn.onclick = () => {{
                    if (audio.paused) {{ 
                        audio.play(); 
                        document.getElementById('lbl').innerText="播放中";
                        document.getElementById('ico').innerText="⏸️";
                    }} else {{ 
                        audio.pause(); 
                        document.getElementById('lbl').innerText="收聽快報";
                        document.getElementById('ico').innerText="▶️";
                    }}
                }};
                
                // 將 audio 對象暴露給 window，讓下方的腳本能讀到它
                window.parent.audioObj = audio;
            </script>
            """
            with col3:
                components.html(btn_html, height=50)

            # --- 🔥 下方主顯示區 (PDF + 進度條 + 字幕) 🔥 ---
            main_display_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body {{ font-family: 'PingFang TC', sans-serif; margin: 0; padding: 0; background: white; }}
                .pdf-view {{ width: 100%; border-radius: 8px; overflow: hidden; border: 1px solid #eee; }}
                .pdf-img {{ width: 100%; display: block; }}
                
                .seek-bar-container {{
                    width: 100%;
                    padding: 10px 0;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}
                input[type=range] {{ flex: 1; accent-color: #1d4ed8; cursor: pointer; }}
                .time-box {{ font-size: 12px; color: #64748b; min-width: 70px; text-align: right; }}

                .bubble-box {{
                    background: #fff9f0;
                    border: 2px dashed #fed7aa;
                    border-radius: 15px;
                    padding: 15px;
                    min-height: 60px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    margin-top: 5px;
                }}
                .text {{ font-size: 19px; color: #1e293b; text-align: center; opacity: 0; transition: opacity 0.2s; }}
                .tag {{ font-weight: bold; font-size: 13px; color: #ea580c; margin-bottom: 3px; }}
            </style>
            </head>
            <body>
                <div class="pdf-view"><img src="data:image/png;base64,{pdf_b64}" class="pdf-img"></div>
                
                <div class="seek-bar-container">
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
                    const seek = document.getElementById('seek');
                    const bubble = document.getElementById('bubble');
                    const script = {script_json_data};
                    
                    // 關鍵：從 window.parent 抓取上面那個組件的 audio 對象
                    let audio;
                    const checkAudio = setInterval(() => {{
                        audio = window.parent.document.querySelector('audio');
                        if (audio) {{
                            setupAudio();
                            clearInterval(checkAudio);
                        }}
                    }}, 500);

                    function fmt(s) {{
                        const m = Math.floor(s/60);
                        const sec = Math.floor(s%60);
                        return m + ":" + (sec < 10 ? "0":"") + sec;
                    }}

                    function setupAudio() {{
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
                                }
                            }}
                            if (!hit) bubble.style.opacity = 0;
                        }};

                        seek.oninput = () => {{ audio.currentTime = seek.value; }};
                    }}
                </script>
            </body>
            </html>
            """
            components.html(main_display_html, height=1000)

        except Exception as e:
            st.error(f"連線異常: {e}")
