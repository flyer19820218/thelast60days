import streamlit as st
import pandas as pd
import requests
import fitz
import streamlit.components.v1 as components
import json
import base64

# ==========================================
# 1. 頁面設定
# ==========================================
st.set_page_config(page_title="會考自然-教學滿版", layout="wide")

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

@st.cache_data(ttl=60)
def load_data():
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
    try:
        return pd.read_csv(SHEET_URL)
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
df = load_data()

if df is not None:
    # 建立一個選單列
    c_unit, c_prev, c_next, c_page = st.columns([2, 0.5, 0.5, 1])
    
    unit_list = df['Day'].tolist()
    with c_unit:
        selected_day = st.selectbox("進度", unit_list, label_visibility="collapsed")
    
    # 頁碼控制 (使用 session_state 確保換頁會觸發重新渲染)
    if 'page_idx' not in st.session_state:
        st.session_state.page_idx = 0

    with c_prev:
        if st.button("⬅️"):
            st.session_state.page_idx = max(0, st.session_state.page_idx - 1)
    with c_next:
        if st.button("➡️"):
            st.session_state.page_idx += 1
    with c_page:
        st.write(f"目前頁碼: {st.session_state.page_idx + 1}")

    # 根據「頁碼」去 DataFrame 找對應的那一橫列資料
    # 假設你的 CSV 裡，每一列代表一個頁碼的資料
    try:
        row = df.iloc[st.session_state.page_idx]
        audio_path = str(row['Audio_Path']).strip().lstrip('/')
        audio_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path}"
        json_url = audio_url.replace('.mp3', '_script.json')
        
        # 準備 PDF
        pdf_b64 = get_pdf_page_as_base64("notes.pdf", st.session_state.page_idx)
        
        # 抓取字幕 JSON
        res_json = requests.get(json_url)
        script_data = res_json.text if res_json.status_code == 200 else "[]"

        # --- 🔥 修正版：換頁即重載音檔的 HTML 🔥 ---
        # 關鍵點：在 HTML 裡加入 key={st.session_state.page_idx} 的概念並非 Streamlit 原生，
        # 但透過 Python 重新生成此字串，HTML 元件會被強迫重新整理
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{ font-family: sans-serif; margin: 0; padding: 0; background: white; }}
            .header-bar {{ display: flex; align-items: center; justify-content: space-between; padding: 10px 20px; border-bottom: 1px solid #f0f0f0; }}
            .title {{ color: #1d4ed8; font-size: 34px; font-weight: bold; margin: 0; }}
            .play-btn {{ background: linear-gradient(135deg, #2b58db, #1d4ed8); color: white; padding: 10px 25px; border-radius: 50px; font-weight: bold; font-size: 18px; cursor: pointer; border: none; }}
            .pdf-container {{ width: 100%; }}
            .pdf-img {{ width: 100%; display: block; }}
            .seek-panel {{ width: 100%; background: #fdfdfd; padding: 10px 20px; display: flex; align-items: center; gap: 15px; box-sizing: border-box; border-bottom: 1px solid #eee; }}
            input[type=range] {{ flex: 1; accent-color: #1d4ed8; cursor: pointer; }}
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
                <div class="title">🚀 考前60天衝刺</div>
                <button id="pBtn" class="play-btn">▶️立刻收聽</button>
            </div>
            <audio id="aud" src="{audio_url}"></audio>
            <div class="pdf-container"><img src="data:image/png;base64,{pdf_b64}" class="pdf-img"></div>
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
        # 這裡加上 key 確保 Streamlit 偵測到變化會重新刷組件
        components.html(full_html, height=1800, scrolling=True)

    except IndexError:
        st.warning("已到達最後一頁或該頁尚無資料。")
    except Exception as e:
        st.error(f"連線異常: {e}")
