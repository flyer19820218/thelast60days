import streamlit as st
import pandas as pd
import requests
import fitz  # PyMuPDF
import streamlit.components.v1 as components
import json

# ==========================================
# 1. 頁面與基礎設定
# ==========================================
st.set_page_config(page_title="國中自然60天逆襲", layout="centered")

# 魔改 CSS：讓整個頁面看起來乾淨，並且設定字體
st.markdown("""
    <style>
    .main { background-color: white; }
    html, body, [class*="css"], p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

USER = "flyer19820218"
REPO = "thelast60days"
GITHUB_RAW = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/"

@st.cache_data(ttl=60)
def load_data():
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
    try:
        df = pd.read_csv(SHEET_URL)
        return df
    except:
        return None

@st.cache_data(ttl=3600)
def get_pdf_page_image(local_pdf_path, page_index):
    try:
        doc = fitz.open(local_pdf_path)
        if page_index >= doc.page_count:
            doc.close()
            return "PAGE_OUT_OF_RANGE"
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0)) 
        img_data = pix.tobytes("png")
        import base64
        # 轉成 base64 讓 CSS 可以直接讀取
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        doc.close()
        return img_base64
    except Exception as e:
        return str(e)

# ==========================================
# 主介面
# ==========================================
# 控制台區域 (隱藏一點，讓視覺集中在 PDF)
with st.expander("🛠️ 進度與講義控制", expanded=False):
    df = load_data()
    if df is not None:
        unit_list = df['Day'].tolist()
        selected = st.selectbox("📅 選擇今日進度", unit_list)
        row = df[df['Day'] == selected].iloc[0]
        st.caption(f"📍 {row['Title']}")
        target_page = st.number_input("翻閱講義頁碼", min_value=1, value=1)
    else:
        st.error("資料載入失敗")
        st.stop()

# --- 💡 終極魔法：疊羅漢互動區 ---
local_pdf_path = "notes.pdf" 
with st.spinner("⏳ 光速載入講義互動中..."):
    pdf_img_base64 = get_pdf_page_image(local_pdf_path, target_page - 1)
    
    if isinstance(pdf_img_base64, str) and len(pdf_img_base64) > 100:
        # 抓取音檔與 JSON 檔的網址
        audio_path = str(row['Audio_Path']).strip()
        if audio_path.startswith('/'): audio_path = audio_path[1:]
        audio_url = f"{GITHUB_RAW}{audio_path}"
        json_url = f"{GITHUB_RAW}{audio_path.replace('.mp3', '_script.json')}"
        
        try:
            # 下載 JSON 時間軸資料
            res_json = requests.get(json_url)
            res_json.raise_for_status()
            script_data_str = res_json.text
            
            # 🔥 HTML + CSS + JS 疊羅漢播放器 🔥
            # 這個 HTML 會把 PDF 當背景，把播放器跟字幕浮在上面！
            html_player = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body {{ font-family: 'PingFang TC', sans-serif; margin: 0; padding: 0; overflow: hidden; }}
                
                /* PDF 背景容器 */
                .pdf-background {{
                    position: relative;
                    width: 100%;
                    /* 這裡會根據 PDF 圖片自動撐開高度 */
                    background-image: url('data:image/png;base64,{pdf_img_base64}');
                    background-size: contain;
                    background-repeat: no-repeat;
                    background-position: center top;
                }}
                
                /* 為了讓容器有高度，我們放一個透明圖片來撐開 */
                .pdf-spacer {{
                    width: 100%;
                    display: block;
                    visibility: hidden;
                }}

                /* 互動元素容器 (浮在 PDF 下半部) */
                .interaction-overlay {{
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    width: 100%;
                    # background: linear-gradient(to bottom, rgba(255,255,255,0), rgba(255,255,255,0.9) 30%); /* 底部加一點白色漸層，保證播放器清晰 */
                    padding: 20px 0;
                    box-sizing: border-box;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                }}

                /* 播放器本體 (帶有半透明) */
                audio {{
                    width: 80%;
                    margin-bottom: 20px;
                    opacity: 0.7; /* 半透明 */
                    transition: opacity 0.3s;
                }}
                audio:hover {{ opacity: 1; }} /* 滑鼠移上去變不透明 */

                /* 泡泡顯示區 */
                .bubble-container {{
                    width: 90%;
                    min-height: 100px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }}
                .bubble {{
                    padding: 15px 20px;
                    border-radius: 20px;
                    max-width: 80%;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                    font-size: 18px;
                    line-height: 1.5;
                    opacity: 0;
                    transition: opacity 0.3s ease-in-out;
                }}
                .yanjun {{
                    background-color: rgba(227, 242, 253, 0.85); /* 半透明藍 */
                    color: #0d47a1;
                    border-bottom-left-radius: 5px;
                    align-self: flex-start;
                }}
                .xiaozhen {{
                    background-color: rgba(255, 243, 224, 0.85); /* 半透明橘 */
                    color: #e65100;
                    border-bottom-right-radius: 5px;
                    align-self: flex-end;
                }}
                .speaker-name {{ font-size: 14px; font-weight: bold; margin-bottom: 5px; opacity: 0.8; }}
            </style>
            </head>
            <body>
                <div class="pdf-background">
                    <img src="data:image/png;base64,{pdf_img_base64}" class="pdf-spacer">

                    <div class="interaction-overlay">
                        <audio id="podcastAudio" controls>
                            <source src="{audio_url}" type="audio/mpeg">
                        </audio>

                        <div class="bubble-container">
                            <div id="bubbleContent" class="bubble yanjun">
                                <div id="speakerName" class="speaker-name">👨‍🏫 準備中...</div>
                                <div id="chatText">點擊播放鍵，衝刺劇本即將彈出！</div>
                            </div>
                        </div>
                    </div>
                </div>

                <script>
                    const audio = document.getElementById('podcastAudio');
                    const bubbleContent = document.getElementById('bubbleContent');
                    const speakerName = document.getElementById('speakerName');
                    const chatText = document.getElementById('chatText');
                    
                    // 接收 JSON 時間軸
                    const scriptData = {script_data_str};

                    audio.addEventListener('timeupdate', () => {{
                        const now = audio.currentTime;
                        let isTalking = false;

                        for (let i = 0; i < scriptData.length; i++) {{
                            if (now >= scriptData[i].start && now <= scriptData[i].end) {{
                                chatText.innerText = scriptData[i].text;
                                
                                if (scriptData[i].speaker === "彥君") {{
                                    speakerName.innerText = "👨‍🏫 彥君老師";
                                    bubbleContent.className = "bubble yanjun";
                                }} else {{
                                    speakerName.innerText = "👩‍🔬 曉臻助教";
                                    bubbleContent.className = "bubble xiaozhen";
                                }}
                                
                                bubbleContent.style.opacity = 1;
                                isTalking = true;
                                break;
                            }}
                        }}

                        if (!isTalking) {{
                            bubbleContent.style.opacity = 0;
                        }}
                    }});
                    
                    // 顯示初始提示
                    bubbleContent.style.opacity = 1;
                </script>
            </body>
            </html>
            """
            
            # 計算 HTML 元件的高度，這裡需要根據 PDF 的長寬比調整，先預設一個大高度
            components.html(html_player, height=900)

        except Exception as e:
            st.error(f"⚠️ 字幕載入失敗，請檢查 {json_url}。(錯誤: {e})")
    else:
        st.error(f"講義圖檔載入失敗: {pdf_img_base64}")
