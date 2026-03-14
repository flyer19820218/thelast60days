import streamlit as st
import pandas as pd
import requests
import fitz
import streamlit.components.v1 as components
import base64
import time

# 1. 頁面設定
st.set_page_config(page_title="會考自然-iPad教學版", layout="wide")

st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .stApp { background-color: #ffffff; }
    html, body, [class*="css"], p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 資料讀取 (移除 cache_data，每次點擊都重新執行)
def load_data_raw():
    url = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
    try:
        # 在網址後加個變數，讓伺服器每次都吐新的
        r = requests.get(f"{url}&nocache={time.time()}")
        from io import StringIO
        return pd.read_csv(StringIO(r.text), encoding='utf-8')
    except:
        return None

def get_pdf_page_as_base64(local_pdf_path, page_index):
    try:
        doc = fitz.open(local_pdf_path)
        page = doc.load_page(page_index)
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
    c1, c2 = st.columns([2, 1])
    
    with c1:
        total_rows = len(df)
        page_list = [f"第 {i+1} 頁" for i in range(total_rows)]
        selected_page_str = st.selectbox("🎯 選擇教學頁碼", page_list)
        page_idx = page_list.index(selected_page_str)
    
    with c2:
        # 用一個大按鈕來強行重整頁面
        if st.button("🔄 同步 GitHub 最新檔案", use_container_width=True):
            st.rerun()

    # 抓取該頁資料
    row = df.iloc[page_idx]
    audio_file = str(row['Audio_Path']).strip().lstrip('/')
    
    # 打破 GitHub CDN 快取
    ts = int(time.time() * 1000)
    audio_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_file}?v={ts}"
    json_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_file.replace('.mp3', '_script.json')}?v={ts}"
    
    pdf_b64 = get_pdf_page_as_base64("notes.pdf", page_idx)
    
    # 字幕讀取
    res_json = requests.get(json_url)
    script_data = res_json.text if res_json.status_code == 200 else "[]"

    # --- HTML 渲染 (移除 key 避免 TypeError) ---
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ font-family: sans-serif; margin: 0; padding: 0; background: white; }}
        .header-bar {{ display: flex; align-items: center; justify-content: space-between; padding: 10px 20px; border-bottom: 2px solid #1d4ed8; }}
        .title {{ color: #1d4ed8; font-size: 32px; font-weight: bold; margin: 0; }}
        .play-btn {{ background: #1d4ed8; color: white; padding: 12px 30px; border-radius: 50px; font-weight: bold; font-size: 20px; cursor: pointer; border: none; }}
        .pdf-view {{ width: 100%; }}
        .pdf-img {{ width: 100%; display: block; }}
        .seek-panel {{ width: 100%; background: #f1f5f9; padding: 15px 25px; display: flex; align-items: center; gap: 20px; box-sizing: border-box; }}
        input[type=range] {{ flex: 1; accent-color: #1d4ed8; cursor: pointer; height: 12px; }}
        .time-box {{ font-size: 16px; color: #475569; min-width: 100px; text-align: right; font-weight: bold; }}
        .subtitle-stage {{ width: 100%; min-height: 200px; display: flex; flex-direction: column; padding: 25px; box-sizing: border-box; }}
        .bubble {{ max-width: 80%; padding: 22px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); font-size: 28px; line-height: 1.6; opacity: 0; transition: all 0.2s ease; }}
        .yanjun {{ align-self: flex-start; background: #e0f2fe; color: #0369a1; border: 2px solid #bae6fd; }}
        .xiaozhen {{ align-self: flex-end; background: #fff1f2; color: #be123c; border: 2px solid #fecdd3; }}
        .name {{ font-size: 16px; font-weight: bold; margin-bottom: 8px; }}
    </style>
    </head>
    <body>
        <div class="header-bar">
            <div class="title">📖 {selected_page_str} 教學</div>
            <button id="pBtn" class="play-btn">▶️ 開始播放</button>
        </div>
        
        <div id="audio-box"></div>
        
        <div class="pdf-view"><img src="data:image/png;base64,{pdf_b64}" class="pdf-img"></div>
        
        <div class="seek-panel">
            <input type="range" id="sk" value="0" step="0.1">
            <div class="time-box"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
        </div>
        
        <div class="subtitle-stage">
            <div id="bubble" class="bubble yanjun"><div id="spk" class="name"></div><div id="msg"></div></div>
        </div>

        <script>
            // 用 JS 動態生成 Audio 標籤，徹底殺掉快取
            const box = document.getElementById('audio-box');
            const aud = document.createElement('audio');
            aud.src = "{audio_url}";
            aud.id = "main_audio";
            aud.preload = "auto";
            box.appendChild(aud);

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
    # 這裡絕對不加 key，避免 TypeError
    components.html(full_html, height=1800, scrolling=True)

else:
    st.error("❌ 無法連線至 Google Sheet，請檢查網路。")
