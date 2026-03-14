import streamlit as st
import pandas as pd
import requests
import fitz
import streamlit.components.v1 as components
import base64
import time

# ==========================================
# 1. 頁面設定
# ==========================================
st.set_page_config(page_title="會考自然-旗艦教學戰車", layout="wide")

st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .stApp { background: #ffffff; }
    html, body, [class*="css"], p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
    }
</style>
""", unsafe_allow_html=True)

def load_data_raw():
    url = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
    try:
        r = requests.get(f"{url}&nocache={time.time()}")
        from io import StringIO
        return pd.read_csv(StringIO(r.text))
    except:
        return None

def get_pdf_page_64(page_idx):
    try:
        doc = fitz.open("notes.pdf")
        page = doc.load_page(page_idx)
        pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0)) 
        return base64.b64encode(pix.tobytes("png")).decode('utf-8')
    except:
        return ""

# ==========================================
# 2. 佈局實作
# ==========================================
df = load_data_raw()

if df is not None:
    if 'page_idx' not in st.session_state:
        st.session_state.page_idx = 0

    # 為了讓 Python 的 selectbox 跟 HTML 能通訊，我們保留 Streamlit 的選擇器但優化佈局
    # 將頁碼選擇器做成一個橫向的控制列
    c1, c2 = st.columns([1, 1])
    
    # 抓取該頁資料
    try:
        row = df.iloc[st.session_state.page_idx]
        audio_file = str(row['Audio_Path']).strip().lstrip('/')
        ts = int(time.time() * 1000)
        audio_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_file}?v={ts}"
        json_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_file.replace('.mp3', '_script.json')}?v={ts}"
        pdf_b64 = get_pdf_page_64(st.session_state.page_idx)
        res_json = requests.get(json_url)
        script_data = res_json.text if res_json.status_code == 200 else "[]"

        # 這裡我們要把選擇器包進 HTML，但 Streamlit 的 selectbox 無法直接塞進去
        # 所以我們在 Python 層做選擇，HTML 層做顯示與播放，讓視覺合一
        
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{ font-family: sans-serif; margin: 0; padding: 0; background: white; }}
            
            /* 🚀 三位一體導航列 */
            .nav-bar {{ 
                display: flex; align-items: center; justify-content: space-between; 
                padding: 15px 30px; background: #f8fafc; border-bottom: 4px solid #1e40af;
                position: sticky; top: 0; z-index: 100;
            }}
            
            .nav-left {{ display: flex; align-items: center; gap: 15px; }}
            .nav-title {{ color: #1e40af; font-size: 26px; font-weight: 900; white-space: nowrap; }}
            
            .nav-center {{ 
                background: #ffffff; border: 2px solid #1e40af; border-radius: 10px;
                padding: 8px 20px; font-size: 20px; font-weight: bold; color: #1e40af;
                box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
            }}

            .play-btn {{ 
                background: #1e40af; color: white; padding: 12px 35px; border-radius: 50px; 
                border: none; font-size: 22px; font-weight: bold; cursor: pointer;
                transition: transform 0.1s;
            }}
            .play-btn:active {{ transform: scale(0.95); }}

            .pdf-view {{ width: 100%; }}
            .pdf-img {{ width: 100%; display: block; }}
            
            .seek-panel {{ 
                width: 100%; background: #f1f5f9; padding: 20px 30px; 
                display: flex; align-items: center; gap: 20px; box-sizing: border-box; 
            }}
            input[type=range] {{ flex: 1; accent-color: #1e40af; height: 18px; cursor: pointer; }}
            .time-box {{ font-size: 20px; color: #1e293b; min-width: 120px; text-align: right; font-family: monospace; font-weight: bold; }}
            
            .subtitle-stage {{ width: 100%; min-height: 220px; display: flex; flex-direction: column; padding: 30px; box-sizing: border-box; }}
            .bubble {{ 
                max-width: 85%; padding: 25px; border-radius: 25px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.08); font-size: 32px; line-height: 1.5; 
                opacity: 0; transition: 0.2s ease; 
            }}
            .yj {{ align-self: flex-start; background: #e0f2fe; color: #0369a1; border: 2px solid #bae6fd; }}
            .xz {{ align-self: flex-end; background: #fff1f2; color: #be123c; border: 2px solid #fecdd3; }}
        </style>
        </head>
        <body>
            <div class="nav-bar">
                <div class="nav-left">
                    <span class="nav-title">🚀 教學模式</span>
                    <div class="nav-center">第 {st.session_state.page_idx + 1} 頁</div>
                </div>
                <button id="pBtn" class="play-btn">▶️ 開始講解</button>
            </div>

            <audio id="aud" src="{audio_url}" preload="auto"></audio>
            
            <div class="pdf-view"><img src="data:image/png;base64,{pdf_b64}" class="pdf-img"></div>
            
            <div class="seek-panel">
                <input type="range" id="sk" value="0" step="0.1">
                <div class="time-box"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
            </div>
            
            <div class="subtitle-stage">
                <div id="bb" class="bubble yj"></div>
            </div>

            <script>
                const aud = document.getElementById('aud');
                const pBtn = document.getElementById('pBtn');
                const sk = document.getElementById('sk');
                const bb = document.getElementById('bb');
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
                            bb.innerText = s.text;
                            bb.className = "bubble " + (s.speaker === '彥君' ? 'yj' : 'xz');
                            bb.style.opacity = 1;
                            hit = true; break;
                        }}
                    }}
                    if(!hit) bb.style.opacity = 0;
                }};

                sk.oninput = () => aud.currentTime = sk.value;
                function fmt(s) {{ return Math.floor(s/60) + ":" + String(Math.floor(s%60)).padStart(2,'0'); }}
            </script>
        </body>
        </html>
        """

        # Python 層的選擇器放在 HTML 上方，但我們用 CSS 隱藏它的一部分或讓它看起來像整合在一起
        page_labels = [f"第 {i+1} 頁" for i in range(len(df))]
        selected_label = st.selectbox("切換頁碼 (iPad 點擊此處)", page_labels, index=st.session_state.page_idx)
        
        new_idx = page_labels.index(selected_label)
        if new_idx != st.session_state.page_idx:
            st.session_state.page_idx = new_idx
            st.rerun()

        components.html(full_html, height=2200, scrolling=True)

    except Exception as e:
        st.error(f"系統異常：{e}")
