import streamlit as st
import pandas as pd
import requests
import fitz
import streamlit.components.v1 as components
import json
import base64

# 1. 頁面設定 (強制全寬模式)
st.set_page_config(page_title="會考自然-教師上課版", layout="wide")

st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .stApp { background-color: #0e1117; color: white; } /* 酷炫深色教學模式 */
    
    /* 讓 PDF 容器變得超級大 */
    .reportview-container .main .block-container { padding-top: 1rem; }
    
    html, body, [class*="css"], p, span, div, b {
        font-family: 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
    }
    
    /* 教師專用控制列樣式 */
    .teacher-bar {
        background: rgba(255,255,255,0.05);
        padding: 10px 20px;
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 資料載入 (維持原有機制)
@st.cache_data(ttl=60)
def load_data():
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
    return pd.read_csv(SHEET_URL)

def get_pdf_page_as_base64(local_pdf_path, page_index):
    doc = fitz.open(local_pdf_path)
    page = doc.load_page(page_index)
    pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0)) # 教學版給 3.0 倍解析度，投影片才清晰
    img_data = pix.tobytes("png")
    doc.close()
    return base64.b64encode(img_data).decode('utf-8')

df = load_data()

if df is not None:
    # --- 頂部教師控制列 ---
    with st.container():
        st.markdown('<div class="teacher-bar">', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1.5])
        
        unit_list = df['Day'].tolist()
        selected_day = c1.selectbox("📅 單元選擇", unit_list, label_visibility="collapsed")
        row = df[df['Day'] == selected_day].iloc[0]
        
        # 翻頁邏輯
        if 'page' not in st.session_state: st.session_state.page = 1
        
        def change_page(delta): st.session_state.page += delta
        
        with c2: st.button("⬅️ 上一頁", on_click=change_page, args=(-1,))
        with c3: st.button("下一頁 ➡️", on_click=change_page, args=(1,))
        
        audio_path = str(row['Audio_Path']).strip().lstrip('/')
        audio_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path}"
        json_url = audio_url.replace('.mp3', '_script.json')
        
        st.markdown('</div>', unsafe_allow_html=True)

    # 準備 PDF
    pdf_b64 = get_pdf_page_as_base64("notes.pdf", st.session_state.page - 1)
    res_json = requests.get(json_url)
    script_json = res_json.text if res_json.status_code == 200 else "[]"

    # --- 🔥 教師版大螢幕 HTML 🔥 ---
    teacher_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ background: #0e1117; color: white; margin: 0; padding: 0; overflow: hidden; }}
        
        .layout {{ display: flex; height: 100vh; gap: 20px; padding: 10px; box-sizing: border-box; }}
        
        /* 左側：巨大講義區 */
        .pdf-section {{ flex: 3; position: relative; background: #1e1e1e; border-radius: 15px; overflow: hidden; display: flex; align-items: center; justify-content: center; }}
        .pdf-img {{ max-height: 100%; max-width: 100%; object-fit: contain; }}

        /* 右側：教學輔助區 */
        .side-section {{ flex: 1; display: flex; flex-direction: column; gap: 20px; }}
        
        .play-card {{ background: #252525; padding: 20px; border-radius: 15px; border-left: 5px solid #3b82f6; }}
        .btn-play {{ background: #3b82f6; color: white; border: none; padding: 12px; width: 100%; border-radius: 10px; font-weight: bold; cursor: pointer; font-size: 18px; }}
        
        .subtitle-card {{ background: #1a1a1a; flex-grow: 1; padding: 20px; border-radius: 15px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #333; }}
        .bubble {{ font-size: 24px; line-height: 1.6; text-align: center; opacity: 0; transition: opacity 0.3s; }}
        .name {{ font-size: 16px; color: #94a3b8; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 2px; }}
        .yanjun {{ color: #60a5fa; }}
        .xiaozhen {{ color: #f87171; }}

        input[type=range] {{ width: 100%; accent-color: #3b82f6; margin-top: 15px; }}
    </style>
    </head>
    <body>
        <div class="layout">
            <div class="pdf-section">
                <img src="data:image/png;base64,{pdf_b64}" class="pdf-img">
            </div>
            
            <div class="side-section">
                <div class="play-card">
                    <button id="pBtn" class="btn-play">▶️ 開始教學演示</button>
                    <input type="range" id="sk" value="0" step="0.1">
                    <div style="text-align:right; font-size:12px; margin-top:5px; color:#666;"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
                </div>

                <div class="subtitle-card">
                    <div id="spk" class="name"></div>
                    <div id="msg" class="bubble"></div>
                </div>
            </div>
        </div>

        <audio id="aud" src="{audio_url}"></audio>

        <script>
            const aud = document.getElementById('aud');
            const pBtn = document.getElementById('pBtn');
            const sk = document.getElementById('sk');
            const msg = document.getElementById('msg');
            const spk = document.getElementById('spk');
            const script = {script_json};

            pBtn.onclick = () => {{
                if(aud.paused) {{ aud.play(); pBtn.innerText = "⏸️ 暫停演示"; }}
                else {{ aud.pause(); pBtn.innerText = "▶️ 繼續演示"; }}
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
                        spk.innerText = (s.speaker === "彥君" ? "👨‍🏫 彥君老師正在說明..." : "👩‍🔬 曉臻助教提問中...");
                        spk.className = "name " + (s.speaker === "彥君" ? "yanjun" : "xiaozhen");
                        msg.innerText = s.text;
                        msg.style.opacity = 1;
                        hit = true; break;
                    }}
                }}
                if(!hit) msg.style.opacity = 0;
            }};

            sk.oninput = () => aud.currentTime = sk.value;
            function fmt(s) {{ return Math.floor(s/60) + ":" + String(Math.floor(s%60)).padStart(2,'0'); }}
        </script>
    </body>
    </html>
    """
    components.html(teacher_html, height=800)
