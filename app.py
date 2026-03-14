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
    .stApp { background-color: #f8f9fa; }
    
    html, body, [class*="css"], p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
    }
    
    /* 選單區容器 */
    .menu-box {
        background-color: white;
        padding: 15px 25px;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    
    /* 讓選單裡的按鈕對齊 */
    div[data-testid="column"] {
        display: flex;
        align-items: center;
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
# 2. 主介面邏輯
# ==========================================
df = load_data()

if df is not None:
    # --- 頂部控制區：整合按鈕與選單 ---
    st.markdown('<div class="menu-box">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2, 1, 1.2]) # 增加一格放按鈕的暗示位置
    unit_list = df['Day'].tolist()
    selected = c1.selectbox("📅 今日進度", unit_list, label_visibility="collapsed")
    row = df[df['Day'] == selected].iloc[0]
    target_page = c2.number_input("📄 頁碼", min_value=1, value=1, label_visibility="collapsed")
    
    # 在 Streamlit 層級我們先放一個佔位標題，按鈕我們待會用 HTML 畫在 PDF 頂部或緊接其後
    st.markdown('</div>', unsafe_allow_html=True)

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

            # --- 🔥 HTML/JS 緊湊互動佈局 🔥 ---
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body {{ font-family: 'PingFang TC', sans-serif; margin: 0; padding: 0; background: #f8f9fa; }}
                
                .main-container {{ max-width: 800px; margin: 0 auto; }}

                /* PDF 區 */
                .pdf-view {{
                    width: 100%;
                    background: white;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    border-radius: 8px 8px 0 0;
                    overflow: hidden;
                }}
                .pdf-img {{ width: 100%; display: block; }}

                /* 緊接 PDF 的互動控制區 (包含字幕、拉桿、按鈕) */
                .control-stage {{
                    background: white;
                    padding: 15px;
                    border-radius: 0 0 15px 15px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }}

                /* 字幕顯示區 */
                .bubble-box {{
                    height: 100px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .bubble {{
                    padding: 12px 20px;
                    border-radius: 15px;
                    font-size: 19px;
                    line-height: 1.5;
                    opacity: 0;
                    transition: opacity 0.3s;
                    width: 90%;
                    text-align: center;
                }}
                .yanjun {{ background-color: #e3f2fd; color: #0d47a1; border: 1px solid #bbdefb; }}
                .xiaozhen {{ background-color: #fff3e0; color: #e65100; border: 1px solid #ffe0b2; }}

                /* 學生控制拉桿 (Seek Bar) */
                .progress-container {{
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    width: 100%;
                }}
                input[type=range] {{
                    flex-grow: 1;
                    cursor: pointer;
                }}
                .time-text {{ font-size: 12px; color: #666; font-family: monospace; }}

                /* 膠囊播放按鈕 (移到上方控制列) */
                .btn-row {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .play-btn {{
                    background: linear-gradient(135deg, #2b58db 0%, #1d4ed8 100%);
                    color: white;
                    padding: 8px 20px;
                    border-radius: 50px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-weight: bold;
                    cursor: pointer;
                    box-shadow: 0 3px 10px rgba(29, 78, 216, 0.3);
                }}
            </style>
            </head>
            <body>
                <div class="main-container">
                    <div class="pdf-view">
                        <img src="data:image/png;base64,{pdf_b64}" class="pdf-img">
                    </div>

                    <div class="control-stage">
                        <div class="btn-row">
                             <div id="btn" class="play-btn">
                                <span id="ico">▶️</span> <span id="lbl">收聽快報</span>
                            </div>
                            <div class="time-text"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
                        </div>

                        <div class="progress-container">
                            <input type="range" id="seekBar" value="0" step="0.1">
                        </div>

                        <div class="bubble-box">
                            <div id="bubble" class="bubble yanjun">
                                <div id="txt">點擊播放，開始今日衝刺！</div>
                            </div>
                        </div>
                    </div>
                </div>

                <audio id="player"><source src="{audio_url}" type="audio/mpeg"></audio>

                <script>
                    const audio = document.getElementById('player');
                    const btn = document.getElementById('btn');
                    const seekBar = document.getElementById('seekBar');
                    const curTime = document.getElementById('cur');
                    const durTime = document.getElementById('dur');
                    const bubble = document.getElementById('bubble');
                    const txt = document.getElementById('txt');
                    const script = {script_json_data};

                    function formatTime(s) {{
                        const m = Math.floor(s / 60);
                        const sec = Math.floor(s % 60);
                        return m + ":" + (sec < 10 ? "0" : "") + sec;
                    }}

                    btn.onclick = () => {{
                        if (audio.paused) {{ audio.play(); document.getElementById('lbl').innerText="播放中"; document.getElementById('ico').innerText="⏸️"; }}
                        else {{ audio.pause(); document.getElementById('lbl').innerText="繼續收聽"; document.getElementById('ico').innerText="▶️"; }}
                    }};

                    audio.onloadedmetadata = () => {{
                        durTime.innerText = formatTime(audio.duration);
                        seekBar.max = audio.duration;
                    }};

                    audio.ontimeupdate = () => {{
                        const t = audio.currentTime;
                        curTime.innerText = formatTime(t);
                        seekBar.value = t;

                        let found = false;
                        for (let s of script) {{
                            if (t >= s.start && t <= s.end) {{
                                txt.innerText = s.text;
                                bubble.className = "bubble " + (s.speaker === "彥君" ? "yanjun" : "xiaozhen");
                                bubble.style.opacity = 1;
                                found = true; break;
                            }}
                        }}
                        if (!found) bubble.style.opacity = 0;
                    }};

                    seekBar.oninput = () => {{
                        audio.currentTime = seekBar.value;
                    }};
                </script>
            </body>
            </html>
            """
            components.html(html_content, height=1200, scrolling=True)
        except Exception as e:
            st.error(f"載入失敗：{e}")
