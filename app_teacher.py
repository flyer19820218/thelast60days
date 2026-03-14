import streamlit as st
import pandas as pd
import requests
import fitz
import streamlit.components.v1 as components
import base64
import time

# ==========================================
# 1. 頁面設定 (iPad Pro 16:9 優化)
# ==========================================
st.set_page_config(page_title="會考自然-iPad教學版", layout="wide")

st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .stApp { background-color: #ffffff; }
    html, body, [class*="css"], p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
    }
    .stSelectbox, .stNumberInput { margin-bottom: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

# 讀取 Google Sheet (不帶 Cache)
def load_data_raw():
    url = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
    try:
        # 使用隨機參數強制 Google Sheet 吐出最新內容
        response = requests.get(f"{url}&cb={time.time()}")
        from io import StringIO
        # 強制指定編碼，預防亂碼
        return pd.read_csv(StringIO(response.text), encoding='utf-8')
    except:
        return None

def get_pdf_page_as_base64(local_pdf_path, page_index):
    try:
        doc = fitz.open(local_pdf_path)
        page = doc.load_page(page_index)
        # iPad 高解析度渲染
        pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0)) 
        img_data = pix.tobytes("png")
        doc.close()
        return base64.b64encode(img_data).decode('utf-8')
    except:
        return ""

# ==========================================
# 2. 佈局實作
# ==========================================
df = load_data_raw()

if df is not None:
    # 頂部控制列：只保留頁碼與功能鍵
    c1, c2, c3 = st.columns([1, 1, 2])
    
    with c1:
        # 建立 1 到 總列數 的頁碼清單
        total_rows = len(df)
        page_list = [f"第 {i+1} 頁" for i in range(total_rows)]
        selected_page_str = st.selectbox("選擇頁碼", page_list, label_visibility="collapsed")
        # 取得索引值
        page_idx = page_list.index(selected_page_str)
    
    with c2:
        # ✨ 關鍵載入按鈕
        load_btn = st.button("🚀 載入教學", use_container_width=True)
    
    with c3:
        # ✨ 強制重整 (錄完音必點)
        if st.button("🔄 同步最新內容 (清除快取)", use_container_width=True):
            st.rerun()

    # --- 邏輯判斷：點擊載入後才顯示 ---
    if load_btn:
        try:
            # 根據索引直接抓取該列資料
            row = df.iloc[page_idx]
            audio_path = str(row['Audio_Path']).strip().lstrip('/')
            
            # 使用時間戳記徹底擊碎 GitHub 與瀏覽器快取
            ts = int(time.time() * 1000)
            audio_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path}?v={ts}"
            json_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path.replace('.mp3', '_script.json')}?v={ts}"
            
            pdf_b64 = get_pdf_page_as_base64("notes.pdf", page_idx)
            
            # 抓取字幕 JSON
            res_json = requests.get(json_url)
            script_data = res_json.text if res_json.status_code == 200 else "[]"

            # --- iPad 滿版 HTML 字幕舞台 ---
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body {{ font-family: sans-serif; margin: 0; padding: 0; background: white; }}
                .header-bar {{ display: flex; align-items: center; justify-content: space-between; padding: 10px 20px; border-bottom: 1px solid #f0f0f0; }}
                .title {{ color: #1d4ed8; font-size: 34px; font-weight: bold; margin: 0; }}
                .play-btn {{ background: linear-gradient(135deg, #2b58db, #1d4ed8); color: white; padding: 10px 25px; border-radius: 50px; font-weight: bold; font-size: 20px; cursor: pointer; border: none; }}
                .pdf-view {{ width: 100%; border-bottom: 2px solid #eee; }}
                .pdf-img {{ width: 100%; display: block; }}
                .seek-panel {{ width: 100%; background: #fdfdfd; padding: 15px 25px; display: flex; align-items: center; gap: 20px; box-sizing: border-box; }}
                input[type=range] {{ flex: 1; accent-color: #1d4ed8; cursor: pointer; height: 12px; }}
                .time-box {{ font-size: 16px; color: #64748b; min-width: 100px; text-align: right; font-weight: bold; }}
                .subtitle-stage {{ width: 100%; min-height: 180px; display: flex; flex-direction: column; padding: 25px; box-sizing: border-box; }}
                .bubble {{ max-width: 75%; padding: 22px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.12); font-size: 28px; line-height: 1.6; opacity: 0; transition: all 0.3s ease; }}
                .yanjun {{ align-self: flex-start; background-color: #e3f2fd; color: #0d47a1; border: 2px solid #bbdefb; border-bottom-left-radius: 2px; }}
                .xiaozhen {{ align-self: flex-end; background-color: #fef2f2; color: #991b1b; border: 2px solid #fecaca; border-bottom-right-radius: 2px; }}
                .name {{ font-size: 16px; font-weight: bold; margin-bottom: 10px; }}
            </style>
            </head>
            <body>
                <div class="header-bar">
                    <div class="title">📖 {selected_page_str} 教學演示</div>
                    <button id="pBtn" class="play-btn">▶️ 開始同步講解</button>
                </div>
                <div id="audio-container"></div>
                <div class="pdf-view"><img src="data:image/png;base64,{pdf_b64}" class="pdf-img"></div>
                <div class="seek-panel">
                    <input type="range" id="sk" value="0" step="0.1">
                    <div class="time-box"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
                </div>
                <div class="subtitle-stage">
                    <div id="bubble" class="bubble yanjun"><div id="spk" class="name"></div><div id="msg"></div></div>
                </div>
                <script>
                    const audioContainer = document.getElementById('audio-container');
                    const aud = document.createElement('audio');
                    aud.src = "{audio_url}";
                    aud.preload = "auto";
                    audioContainer.appendChild(aud);

                    const pBtn = document.getElementById('pBtn');
                    const sk = document.getElementById('sk');
                    const bubble = document.getElementById('bubble');
                    const spk = document.getElementById('spk');
                    const msg = document.getElementById('msg');
                    const script = {script_data};

                    pBtn.onclick = () => {{
                        if(aud.paused) {{ aud.play(); pBtn.innerText = "⏸️ 暫停"; }}
                        else {{ aud.pause(); pBtn.innerText = "▶️ 繼續"; }}
                    }};
                    aud.onloadedmetadata = () => {{
                        document.getElementById('dur').innerText = fmt(aud.duration);
                        sk.max = aud.duration;
                    }};
                    aud.ontimeupdate = () => {{
                        const t = aud.currentTime;
                        document.getElementById('cur').innerText = fmt(t);
                        sk.value = t;
                        let hit = false;
                        for(let s of script) {{
                            if(t >= s.start && t <= s.end) {{
                                spk.innerText = (s.speaker === '彥君' ? '👨‍🏫 彥君老師' : '👩‍🔬 曉臻助教');
                                msg.innerText = s.text;
                                bubble.className = "bubble " + (s.speaker === '彥君' ? 'yanjun' : 'xiaozhen');
                                bubble.style.opacity = 1;
                                hit = true; break;
                            }}
                        }}
                        if(!hit) bubble.style.opacity = 0;
                    }};
                    sk.oninput = () => aud.currentTime = sk.value;
                    function fmt(s) {{ return Math.floor(s/60) + ":" + String(Math.floor(s%60)).padStart(2,'0'); }}
                </script>
            </body>
            </html>
            """
            # 強制換頁時重載 HTML 組件
            st.components.v1.html(full_html, height=1800, scrolling=True)
            
        except Exception as e:
            st.error(f"⚠️ 載入出錯：{e}")
    else:
        st.info("💡 戰士請在上方選擇「頁碼」，點擊「🚀 載入教學」開始。")

else:
    st.error("Google Sheet 資料讀取失敗，請確認網路連線。")
