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
    .stApp { background-color: white; }
    
    /* 確保頂部選單有足夠的呼吸空間，不與下方 PDF 碰撞 */
    .stExpander {
        margin-top: 30px;
        margin-bottom: 20px;
        border: 1px solid #ebf0f5;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

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
    # 頂部控制區
    with st.expander("📂 課程進度與講義翻頁", expanded=False):
        unit_list = df['Day'].tolist()
        selected = st.selectbox("📅 選擇今日進度", unit_list)
        row = df[df['Day'] == selected].iloc[0]
        st.write(f"📖 **目前單元**：{row['Title']}")
        target_page = st.number_input("📄 翻閱講義頁碼", min_value=1, value=1)

    # 處理 PDF 講義
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

            # --- 🔥 HTML/CSS 終極佈局 🔥 ---
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body {{ font-family: 'PingFang TC', sans-serif; margin: 0; padding: 0; background: white; }}
                .wrapper {{ position: relative; width: 100%; max-width: 800px; margin: 0 auto; }}
                .pdf-img {{ width: 100%; display: block; border-radius: 4px; }}
                
                .overlay {{
                    position: absolute;
                    bottom: 40px;
                    right: 25px;
                    display: flex;
                    flex-direction: column;
                    align-items: flex-end;
                    gap: 15px;
                }}

                .play-btn {{
                    background: linear-gradient(135deg, #2b58db 0%, #1d4ed8 100%);
                    color: white;
                    padding: 12px 28px;
                    border-radius: 50px;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    font-weight: bold;
                    font-size: 18px;
                    cursor: pointer;
                    box-shadow: 0 6px 20px rgba(29, 78, 216, 0.4);
                    border: 2px solid rgba(255,255,255,0.2);
                    transition: all 0.2s;
                    user-select: none;
                }}
                .play-btn:active {{ transform: scale(0.95); }}

                .bubble-container {{ width: 300px; pointer-events: none; }}
                .bubble {{
                    padding: 15px 20px;
                    border-radius: 20px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.15);
                    font-size: 18px;
                    line-height: 1.5;
                    opacity: 0;
                    transition: opacity 0.3s ease;
                }}
                .yanjun {{ background-color: rgba(227, 242, 253, 0.98); color: #0d47a1; }}
                .xiaozhen {{ background-color: rgba(255, 243, 224, 0.98); color: #e65100; }}
                .name-tag {{ font-size: 13px; font-weight: bold; margin-bottom: 4px; opacity: 0.8; }}
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
            components.html(html_content, height=850, scrolling=False)

        except Exception as e:
            st.error(f"字幕同步失敗：{e}")
    else:
        st.error("講義圖片讀取失敗")
else:
    st.error("Google Sheet 連線失敗")
