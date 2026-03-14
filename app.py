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
    /* 1. 隱藏 Streamlit 原生垃圾元件 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: white; }
    
    /* 2. 徹底重寫選單容器，解決亂碼問題 */
    .stSelectbox, .stNumberInput {
        margin-bottom: 10px;
    }
    
    /* 隱藏那個會產生亂碼圖示的 expander header icon */
    [data-testid="stExpander"] svg {
        display: none;
    }
    
    [data-testid="stExpander"] p {
        font-size: 18px;
        font-weight: bold;
        color: #2b58db;
    }

    /* 3. 全域字體強制執行 */
    html, body, [class*="css"], p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
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
        # 提高倍率至 2.5 確保超清晰
        pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5)) 
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
    # --- 頂部控制面板 ---
    # 使用簡潔的標題，不再放 icon 避免編碼錯誤
    with st.expander("課程進度與講義翻頁", expanded=False):
        unit_list = df['Day'].tolist()
        selected = st.selectbox("📅 選擇今日進度", unit_list)
        row = df[df['Day'] == selected].iloc[0]
        st.info(f"📍 目前單元：{row['Title']}")
        target_page = st.number_input("📄 翻閱講義頁碼", min_value=1, value=1)

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

            # --- 🔥 HTML/JS 視覺引擎 (優化佈局寬度) 🔥 ---
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body {{ font-family: 'PingFang TC', sans-serif; margin: 0; padding: 0; background: white; }}
                .wrapper {{ 
                    position: relative; 
                    width: 100%; 
                    max-width: 750px; /* 稍微縮小寬度，避免手機版破圖 */
                    margin: 0 auto; 
                }}
                .pdf-img {{ width: 100%; display: block; }}
                
                .overlay {{
                    position: absolute;
                    bottom: 30px;
                    right: 20px;
                    display: flex;
                    flex-direction: column;
                    align-items: flex-end;
                    gap: 15px;
                }}

                .play-btn {{
                    background: linear-gradient(135deg, #2b58db 0%, #1d4ed8 100%);
                    color: white;
                    padding: 12px 26px;
                    border-radius: 50px;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    font-weight: bold;
                    font-size: 17px;
                    cursor: pointer;
                    box-shadow: 0 6px 20px rgba(29, 78, 216, 0.4);
                    border: 1px solid rgba(255,255,255,0.3);
                    transition: all 0.2s ease;
                    user-select: none;
                }}
                .play-btn:active {{ transform: scale(0.95); }}

                .bubble-container {{ width: 280px; pointer-events: none; }}
                .bubble {{
                    padding: 15px 18px;
                    border-radius: 18px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.12);
                    font-size: 17px;
                    line-height: 1.6;
                    opacity: 0;
                    transition: opacity 0.3s ease;
                }}
                .yanjun {{ background-color: rgba(227, 242, 253, 0.98); color: #0d47a1; }}
                .xiaozhen {{ background-color: rgba(255, 243, 224, 0.98); color: #e65100; }}
                .name-tag {{ font-size: 12px; font-weight: bold; margin-bottom: 4px; opacity: 0.7; }}
            </style>
            </head>
            <body>
                <div class="wrapper">
                    <img src="data:image/png;base64,{pdf_b64}" class="pdf-img">
                    <audio id="player"><source src="{audio_url}" type="audio/mpeg"></audio>

                    <div class="overlay">
                        <div class="bubble-container">
                            <div id="bubble" class="bubble yanjun">
                                <div id="speaker" class="name-tag">👨‍🏫 彥君老師</div>
                                <div id="txt">準備好了嗎？點擊按鈕開始！</div>
                            </div>
                        </div>
                        <div id="btn" class="play-btn">
                            <span id="ico">▶️</span> <span id="lbl">收聽快報</span>
                        </div>
                    </div>
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
                                }} else {{
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
            # 高度設定 800，scrolling 關閉，讓畫面更像原生 App
            components.html(html_content, height=800, scrolling=False)

        except Exception as e:
            st.error(f"⚠️ 字幕同步失敗：{e}")
    else:
        st.error("❌ 講義圖片生成失敗")
else:
    st.error("❌ 無法連接雲端資料庫")
