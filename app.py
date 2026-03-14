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
    
    /* 強制字體 */
    html, body, [class*="css"], p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
    }
    
    /* 選單區美化 */
    .menu-box {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
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
    # --- 頂部選單區 (捨棄 expander 防止亂碼) ---
    st.markdown('<div class="menu-box">', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    unit_list = df['Day'].tolist()
    selected = c1.selectbox("📅 選擇今日進度", unit_list)
    row = df[df['Day'] == selected].iloc[0]
    target_page = c2.number_input("📄 講義頁碼", min_value=1, value=1)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 處理 PDF 圖片 ---
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

            # --- 🔥 下方字幕區分離佈局 🔥 ---
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body {{ font-family: 'PingFang TC', sans-serif; margin: 0; padding: 0; background: #f8f9fa; }}
                
                .pdf-view {{
                    width: 100%;
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    border-radius: 8px;
                    overflow: hidden;
                }}
                .pdf-img {{ width: 100%; display: block; }}

                /* 專屬字幕舞台 (在 PDF 下方) */
                .subtitle-stage {{
                    width: 100%;
                    max-width: 800px;
                    margin: 20px auto;
                    height: 180px;
                    position: relative;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}

                /* 泡泡設計 */
                .bubble {{
                    padding: 20px 25px;
                    border-radius: 25px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                    font-size: 20px;
                    line-height: 1.6;
                    opacity: 0;
                    transition: all 0.3s ease;
                    width: 85%;
                    text-align: center;
                }}
                .yanjun {{ background-color: #e3f2fd; color: #0d47a1; border: 2px solid #bbdefb; }}
                .xiaozhen {{ background-color: #fff3e0; color: #e65100; border: 2px solid #ffe0b2; }}
                .name-tag {{ font-size: 14px; font-weight: bold; margin-bottom: 8px; }}

                /* 固定在右下角的膠囊按鈕 */
                .btn-fixed {{
                    position: fixed;
                    bottom: 30px;
                    right: 30px;
                    z-index: 1000;
                    background: linear-gradient(135deg, #2b58db 0%, #1d4ed8 100%);
                    color: white;
                    padding: 12px 25px;
                    border-radius: 50px;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    font-weight: bold;
                    cursor: pointer;
                    box-shadow: 0 5px 20px rgba(29, 78, 216, 0.5);
                    user-select: none;
                    transition: transform 0.2s;
                }}
                .btn-fixed:active {{ transform: scale(0.9); }}
            </style>
            </head>
            <body>
                <div class="pdf-view">
                    <img src="data:image/png;base64,{pdf_b64}" class="pdf-img">
                </div>

                <div class="subtitle-stage">
                    <div id="bubble" class="bubble yanjun">
                        <div id="speaker" class="name-tag">👨‍🏫 彥君老師</div>
                        <div id="txt">準備好了嗎？點擊右下角按鈕開始衝刺！</div>
                    </div>
                </div>

                <audio id="player"><source src="{audio_url}" type="audio/mpeg"></audio>

                <div id="btn" class="btn-fixed">
                    <span id="ico">▶️</span> <span id="lbl">收聽快報</span>
                </div>

                <script>
                    const audio = document.getElementById('player');
                    const btn = document.getElementById('btn');
                    const bubble = document.getElementById('bubble');
                    const script = {script_json_data};

                    btn.onclick = () => {{
                        if (audio.paused) {{
                            audio.play();
                            document.getElementById('lbl').innerText = "播放中";
                            document.getElementById('ico').innerText = "⏸️";
                        }} else {{
                            audio.pause();
                            document.getElementById('lbl').innerText = "繼續收聽";
                            document.getElementById('ico').innerText = "▶️";
                        }}
                    }};

                    audio.ontimeupdate = () => {{
                        const t = audio.currentTime;
                        let found = false;
                        for (let s of script) {{
                            if (t >= s.start && t <= s.end) {{
                                document.getElementById('txt').innerText = s.text;
                                if (s.speaker === "彥君") {{
                                    document.getElementById('speaker').innerText = "👨‍🏫 彥君老師";
                                    bubble.className = "bubble yanjun";
                                } else {{
                                    document.getElementById('speaker').innerText = "👩‍🔬 曉臻助教";
                                    bubble.className = "bubble xiaozhen";
                                }}
                                bubble.style.opacity = 1;
                                found = true; break;
                            }}
                        }}
                        if (!found) bubble.style.opacity = 0;
                    }};
                    bubble.style.opacity = 1;
                </script>
            </body>
            </html>
            """
            # 調整高度以適應新的佈局
            components.html(html_content, height=1200, scrolling=True)

        except Exception as e:
            st.error(f"字幕同步失敗：{e}")
