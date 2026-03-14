import streamlit as st
import pandas as pd
import requests
import fitz  
import streamlit.components.v1 as components
import json

# ==========================================
# 1. 頁面與基礎設定
# ==========================================
st.set_page_config(page_title="國中自然60天逆襲", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
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
def get_pdf_page_image(local_pdf_path, page_index):
    try:
        doc = fitz.open(local_pdf_path)
        if page_index >= doc.page_count:
            doc.close()
            return "PAGE_OUT_OF_RANGE"
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0)) 
        img_data = pix.tobytes("png")
        doc.close()
        return img_data
    except Exception as e:
        return str(e)

# ==========================================
# 主介面
# ==========================================
st.title("🎧 自然科學真理 PODCAST")
st.caption("免登入，自動對齊時間軸，極速衝刺！")

df = load_data()

if df is not None:
    unit_list = df['Day'].tolist()
    selected = st.selectbox("📅 選擇今日進度：", unit_list)
    row = df[df['Day'] == selected].iloc[0]

    st.divider()
    st.header(f"📍 {row['Title']}")

    # --- 視覺區：PDF 顯示 ---
    st.subheader("📝 彥君老師手繪講義")
    target_page = st.number_input("翻閱講義頁碼：", min_value=1, value=1)
    local_pdf_path = "notes.pdf" 
    
    with st.spinner("⏳ 光速載入講義圖檔中..."):
        result = get_pdf_page_image(local_pdf_path, target_page - 1)
        if result == "PAGE_OUT_OF_RANGE":
            st.warning(f"⚠️ 這份講義沒有第 {target_page} 頁喔！")
        elif isinstance(result, bytes): 
            st.image(result, use_container_width=True, caption=f"講義第 {target_page} 頁")
        else:
            st.error(f"⚠️ 讀取失敗。系統回報：{result}")

    # --- 💡 終極魔法：動態泡泡播放器 ---
    st.divider()
    st.subheader("💬 動態衝刺劇本 (黃金語速版)")
    
    # 抓取音檔與 JSON 檔的網址
    audio_path = str(row['Audio_Path']).strip()
    if audio_path.startswith('/'): audio_path = audio_path[1:]
    audio_url = f"{GITHUB_RAW}{audio_path}"
    
    # 假設 JSON 檔名跟 MP3 檔名一樣，只是副檔名不同 (例如 p1.mp3 -> p1_script.json)
    json_url = f"{GITHUB_RAW}{audio_path.replace('.mp3', '_script.json')}"
    
    try:
        # 下載 JSON 時間軸資料
        res_json = requests.get(json_url)
        res_json.raise_for_status()
        script_data_str = res_json.text
        
        # 建立 HTML + JS 播放器
        html_player = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{ font-family: 'PingFang TC', sans-serif; margin: 0; padding: 10px; }}
            .bubble-container {{
                height: 180px; 
                display: flex;
                flex-direction: column;
                justify-content: flex-end;
                padding: 10px;
                background-color: #f9f9f9;
                border-radius: 15px;
                border: 2px dashed #ccc;
                margin-top: 15px;
            }}
            .bubble {{
                padding: 15px 20px;
                border-radius: 20px;
                max-width: 90%;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                font-size: 18px;
                line-height: 1.5;
                opacity: 0;
                transition: opacity 0.3s ease-in-out;
            }}
            .yanjun {{
                background-color: #e3f2fd;
                color: #0d47a1;
                border-bottom-left-radius: 5px;
                align-self: flex-start;
            }}
            .xiaozhen {{
                background-color: #fff3e0;
                color: #e65100;
                border-bottom-right-radius: 5px;
                align-self: flex-end;
            }}
            .speaker-name {{ font-size: 14px; font-weight: bold; margin-bottom: 5px; opacity: 0.8; }}
        </style>
        </head>
        <body>
            <audio id="podcastAudio" controls style="width: 100%;">
                <source src="{audio_url}" type="audio/mpeg">
            </audio>

            <div class="bubble-container">
                <div id="bubbleContent" class="bubble yanjun">
                    <div id="speakerName" class="speaker-name">👨‍🏫 準備中...</div>
                    <div id="chatText">點擊上方播放鍵開始衝刺！</div>
                </div>
            </div>

            <script>
                const audio = document.getElementById('podcastAudio');
                const bubbleContent = document.getElementById('bubbleContent');
                const speakerName = document.getElementById('speakerName');
                const chatText = document.getElementById('chatText');
                
                // 這裡接收 Python 傳過來的 JSON 時間軸
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

                    // 沒有人講話時隱藏泡泡
                    if (!isTalking) {{
                        bubbleContent.style.opacity = 0;
                    }}
                }});
                
                // 一開始顯示提示
                bubbleContent.style.opacity = 1;
            </script>
        </body>
        </html>
        """
        
        components.html(html_player, height=300)

    except Exception as e:
        st.error(f"⚠️ 動態字幕載入中或檔案未上傳...請確認 {json_url} 是否存在。(系統回報: {e})")
else:
    st.error("資料庫連線中...")
