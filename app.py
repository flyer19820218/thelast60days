import streamlit as st
import pandas as pd
import requests
import fitz  # PyMuPDF
import streamlit.components.v1 as components
import json
import base64

# ==========================================
# 1. 頁面基礎設定與視覺隱藏
# ==========================================
st.set_page_config(page_title="國中自然60天逆襲", layout="centered")

st.markdown("""
    <style>
    /* 隱藏 Streamlit 原生多餘元件 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: white; }
    
    /* 強制全域字體 */
    html, body, [class*="css"], p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

USER = "flyer19820218"
REPO = "thelast60days"
GITHUB_RAW = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/"

# ==========================================
# 2. 資料載入與 PDF 轉 Base64 圖檔
# ==========================================
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
        # 高解析度渲染
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0)) 
        img_data = pix.tobytes("png")
        doc.close()
        return base64.b64encode(img_data).decode('utf-8')
    except Exception as e:
        return str(e)

# ==========================================
# 3. 主介面邏輯
# ==========================================
df = load_data()

if df is not None:
    # 控制台 (收納起來，讓畫面主體是 PDF)
    with st.expander("🛠️ 進度與講義翻頁控制", expanded=False):
        unit_list = df['Day'].tolist()
        selected = st.selectbox("📅 選擇今日進度", unit_list)
        row = df[df['Day'] == selected].iloc[0]
        st.info(f"📍 目前單元：{row['Title']}")
        target_page = st.number_input("翻閱講義頁碼 (PDF 頁數)", min_value=1, value=1)

    # 準備 PDF 背景圖
    local_pdf_path = "notes.pdf"
    pdf_b64 = get_pdf_page_as_base64(local_pdf_path, target_page - 1)

    if len(pdf_b64) > 500: # 確保有抓到圖
        # 準備音訊與字幕路徑
        audio_path = str(row['Audio_Path']).strip().lstrip('/')
        audio_url = f"{GITHUB_RAW}{audio_path}"
        json_url = f"{GITHUB_RAW}{audio_path.replace('.mp3', '_script.json')}"

        try:
            # 抓取 JSON 時間軸
            res_json = requests.get(json_url)
            res_json.raise_for_status()
            script_json_data = res_json.text

            # --- 🔥 終極疊羅漢 HTML 播放器 🔥 ---
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body {{ font-family: 'PingFang TC', sans-serif; margin: 0; padding: 0; overflow: hidden; }}
                
                /* PDF 背景容器 */
                .container {{
                    position: relative;
                    width: 100%;
                    background-image: url('data:image/png;base64,{pdf_b64}');
                    background-size: contain;
                    background-repeat: no-repeat;
                    background-position: center top;
                }}
                
                /* 透明撐開圖層 */
                .spacer {{ width: 100%; display: block; visibility: hidden; }}

                /* 右下角控制層 */
                .overlay {{
                    position: absolute;
                    bottom: 30px;
                    right: 30px;
                    display: flex;
                    flex-direction: column;
                    align-items: flex-end;
                    gap: 15px;
                    width: 100%;
                }}

                /* 藍色膠囊播放鍵 */
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
                    border: 2px solid rgba(255,255,255,0.3);
                    transition: all 0.2s;
                    user-select: none;
                    margin-right: 30px;
                }}
                .play-btn:hover {{ transform: scale(1.05); filter: brightness(1.1); }}
                .play-btn:active {{ transform: scale(0.95); }}

                /* 浮動字幕泡泡 */
                .bubble-box {{
                    width: 320px;
                    margin-right: 30px;
                    display: flex;
                    flex-direction: column;
                }}
                .bubble {{
                    padding: 15px 20px;
                    border-radius: 20px;
                    box-shadow: 0 8px 30px rgba(0,0,0,0.15);
                    font-size: 18px;
                    line-height: 1.5;
                    opacity: 0;
                    transition: opacity 0.3s ease;
                    border: 1px solid rgba(255,255,255,0.8);
                }}
                .yanjun {{ background-color: rgba(227, 242, 253, 0.96); color: #0d47a1; }}
                .xiaozhen {{ background-color: rgba(255, 243, 224, 0.96); color: #e65100; }}
                .speaker-label {{ font-size: 13px; font-weight: bold; margin-bottom: 4px; opacity: 0.7; }}
            </style>
            </head>
            <body>
                <div class="container">
                    <img src="data:image/png;base64,{pdf_b64}" class="spacer">
                    
                    <audio id="audioTrack"><source src="{audio_url}" type="audio/mpeg"></audio>

                    <div class="overlay">
                        <div class="bubble-box">
                            <div id="bubble" class="bubble yanjun">
                                <div id="speaker" class="speaker-label">👨‍🏫 彥君老師</div>
                                <div id="text">點擊右下方按鈕開始衝刺！</div>
                            </div>
                        </div>

                        <div id="ctrlBtn" class="play-btn">
                            <span id="icon">▶️</span>
                            <span id="label">收聽快報</span>
                        </div>
                    </div>
                </div>

                <script>
                    const audio = document.getElementById('audioTrack');
                    const btn = document.getElementById('ctrlBtn');
                    const icon = document.getElementById('icon');
                    const label = document.getElementById('label');
                    const bubble = document.getElementById('bubble');
                    const speaker = document.getElementById('speaker');
                    const text = document.getElementById('text');
                    
                    const data = {script_json_data};

                    // 播放控制
                    btn.onclick = () => {{
                        if (audio.paused) {{
                            audio.play();
                            label.innerText = "播放中";
                            icon.innerText = "⏸️";
                        }} else {{
                            audio.pause();
                            label.innerText = "繼續收聽";
                            icon.innerText = "▶️";
                        }}
                    }};

                    // 時間軸同步
                    audio.ontimeupdate = () => {{
                        const now = audio.currentTime;
                        let hit = false;
                        for (let item of data) {{
                            if (now >= item.start && now <= item.end) {{
                                text.innerText = item.text;
                                if (item.speaker === "彥君") {{
                                    speaker.innerText = "👨‍🏫 彥君老師";
                                    bubble.className = "bubble yanjun";
                                }} else {{
                                    speaker.innerText = "👩‍🔬 曉臻助教";
                                    bubble.className = "bubble xiaozhen";
                                }}
                                bubble.style.opacity = 1;
                                hit = true;
                                break;
                            }}
                        }}
                        if (!hit) bubble.style.opacity = 0;
                    }};
                    
                    // 初始化顯示
                    bubble.style.opacity = 1;
                </script>
            </body>
            </html>
            """
            # 設定一個較大的高度，確保 PDF 完整顯示
            components.html(html_content, height=1000)

        except Exception as e:
            st.error(f"❌ 字幕同步檔載入失敗，請確認 GitHub 上的 JSON 是否正確。({e})")
    else:
        st.error("❌ PDF 講義渲染失敗，請確認 notes.pdf 是否存在。")
else:
    st.error("❌ 無法讀取 Google Sheet 資料。")
