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
st.set_page_config(page_title="會考自然-旗艦教學版", layout="wide")

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

# 徹底清除緩存的讀取函數
def load_data_no_cache():
    url = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
    try:
        # 在請求頭加入隨機數，確保 Google 給的是最新 CSV
        response = requests.get(f"{url}&nocache={time.time()}")
        from io import StringIO
        return pd.read_csv(StringIO(response.text))
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
df = load_data_no_cache()

if df is not None:
    # 頂部控制列
    c1, c2, c3 = st.columns([2, 1, 1])
    
    with c1:
        unit_list = ["--- 請選擇進度 ---"] + df['Day'].tolist()
        selected_unit = st.selectbox("進度", unit_list, label_visibility="collapsed")
    
    with c2:
        # 提供 1-100 頁供選擇（或動態偵測）
        target_page = st.number_input("目標頁碼", min_value=1, max_value=100, value=1)
    
    with c3:
        # ✨ 關鍵按鈕：點了才載入
        load_btn = st.button("🚀 載入教學內容", use_container_width=True)
        # ✨ 刷新按鈕：清空一切
        if st.button("🔄 強制重新整理", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # --- 邏輯判斷：只有按下載入，或是已經在該頁面上才顯示 ---
    if selected_unit != "--- 請選擇進度 ---" and load_btn:
        try:
            # 取得對應資料
            row = df[df['Day'] == selected_unit].iloc[0]
            audio_path = str(row['Audio_Path']).strip().lstrip('/')
            
            # 使用超長隨機數打破 CDN 快取
            ts = int(time.time())
            audio_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path}?v={ts}"
            json_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path.replace('.mp3', '_script.json')}?v={ts}"
            
            pdf_b64 = get_pdf_page_as_base64("notes.pdf", target_page - 1)
            
            res_json = requests.get(json_url)
            script_data = res_json.text if res_json.status_code == 200 else "[]"

            # --- 教學滿版 HTML ---
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body {{ font-family: sans-serif; margin: 0; padding: 0; background: white; }}
                .header-bar {{ display: flex; align-items: center; justify-content: space-between; padding: 10px 20px; border-bottom: 1px solid #f0f0f0; }}
                .title {{ color: #1d4ed8; font-size: 34px; font-weight: bold; margin: 0; }}
                .play-btn {{ background: linear-gradient(135deg, #2b58db, #1d4ed8); color: white; padding: 10px 25px; border-radius: 50px; font-weight: bold; font-size: 18px; cursor: pointer; border: none; }}
                .pdf-view {{ width: 100%; }}
                .pdf-img {{ width: 100%; display: block; }}
                .seek-panel {{ width: 100%; background: #fdfdfd; padding: 10px 20px; display: flex; align-items: center; gap: 15px; box-sizing: border-box; border-bottom: 1px solid #eee; }}
                input[type=range] {{ flex: 1; accent-color: #1d4ed8; cursor: pointer; height: 10px; }}
                .time-box {{ font-size: 14px; color: #64748b; min-width: 95px; text-align: right; }}
                .subtitle-stage {{ width: 100%; min-height: 150px; display: flex; flex-direction: column; padding: 20px; box-sizing: border-box; }}
                .bubble {{ max-width: 70%; padding: 20px; border-radius: 20px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); font-size: 24px; line-height: 1.5; opacity: 0; transition: all 0.3s ease; }}
                .yanjun {{ align-self: flex-start; background-color: #e3f2fd; color: #0d47a1; border: 2px solid #bbdefb; border-bottom-left-radius: 2px; }}
                .xiaozhen {{ align-self: flex-end; background-color: #fef2f2; color: #991b1b; border: 2px solid #fecaca; border-bottom-right-radius: 2px; }}
                .name {{ font-size: 14px; font-weight: bold; margin-bottom: 8px; }}
            </style>
            </head>
            <body>
                <div class="header-bar">
                    <div class="title">🚀 考前60天衝刺 (頁碼: {target_page})</div>
                    <button id="pBtn" class="play-btn">▶️ 開始同步教學</button>
                </div>
                <audio id="aud" src="{audio_url}" preload="auto"></audio>
                <div class="pdf-view"><img src="data:image/png;base64,{pdf_b64}" class="pdf-img"></div>
                <div class="seek-panel">
                    <input type="range" id="sk" value="0" step="0.1">
                    <div class="time-box"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
                </div>
                <div class="subtitle-stage">
                    <div id="bubble" class="bubble yanjun"><div id="spk" class="name"></div><div id="msg"></div></div>
                </div>
                <script>
                    const aud = document.getElementById('aud');
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
            st.components.v1.html(full_html, height=1800, scrolling=True)
            
        except Exception as e:
            st.error(f"⚠️ 載入出錯：{e}")
    else:
        # 初始畫面提示
        st.info("💡 戰士請先在上方選擇「單元」與「頁碼」，然後點擊「載入教學內容」。")

else:
    st.error("Google Sheet 資料讀取失敗。")
