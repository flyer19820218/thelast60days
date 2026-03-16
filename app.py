import streamlit as st
import pandas as pd
import requests
import fitz
import streamlit.components.v1 as components
import base64
import time
import math

# ==========================================
# 【編號 1】頁面設定與 RWD 響應式 CSS 
# ==========================================
st.set_page_config(page_title="會考自然-旗艦教學版", layout="wide")

st.markdown("""
    <style>
    /* 隱藏 Streamlit 預設介面 */
    #MainMenu, header, footer {visibility: hidden;}
    .stApp { background-color: #ffffff; }
    html, body, [class*="css"], p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
    }
    .stSelectbox, .stNumberInput { margin-bottom: 0px !important; }
    
    /* 📱【手機/平板預設模式】 */
    div[data-baseweb="select"] { font-size: 16px !important; }
    div[data-baseweb="select"] > div { min-height: 40px !important; }
    ul[data-baseweb="menu"] li { font-size: 16px !important; padding: 10px !important; }
    .stButton > button { font-size: 16px !important; min-height: 40px !important; width: 100% !important; padding: 5px !important; }
    
    /* 📺【大電視霸氣模式】 */
    @media (min-width: 1024px) {
        div[data-baseweb="select"] { font-size: 24px !important; }
        div[data-baseweb="select"] > div { min-height: 55px !important; }
        ul[data-baseweb="menu"] li { font-size: 22px !important; padding-top: 15px !important; padding-bottom: 15px !important; }
        .stButton > button { font-size: 24px !important; min-height: 55px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 【編號 2】資料讀取與 PDF 轉檔
# ==========================================
@st.cache_data(ttl=3600)
def load_data_fresh():
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
    try:
        return pd.read_csv(SHEET_URL)
    except:
        return None

def get_pdf_page_as_base64(local_pdf_path, page_index):
    try:
        doc = fitz.open(local_pdf_path)
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)) 
        img_data = pix.tobytes("png")
        doc.close()
        return base64.b64encode(img_data).decode('utf-8')
    except:
        return ""

# ==========================================
# 【編號 3】佈局實作 (控制列邏輯)
# ==========================================
df = load_data_fresh()

if df is not None and not df.empty:
    if 'page_idx' not in st.session_state:
        st.session_state.page_idx = 0

    total_items = len(df)
    group_size = 10
    num_groups = math.ceil(total_items / group_size)
    group_labels = [f"進度 {i*group_size + 1} ~ {min((i+1)*group_size, total_items)}" for i in range(num_groups)]
    current_group_idx = st.session_state.page_idx // group_size

    c_group, c_unit, c_speed, c_size, c_prev, c_next = st.columns([1.5, 2.5, 1.0, 1.0, 0.5, 0.5])
    
    with c_group:
        selected_group = st.selectbox("範圍", group_labels, index=current_group_idx, label_visibility="collapsed")
        new_group_idx = group_labels.index(selected_group)
        if new_group_idx != current_group_idx:
            st.session_state.page_idx = new_group_idx * group_size
            st.rerun()

    with c_unit:
        start_idx = new_group_idx * group_size
        end_idx = min(start_idx + group_size, total_items)
        sub_df = df.iloc[start_idx:end_idx]
        unit_list = sub_df['Title'].tolist()
        local_idx = st.session_state.page_idx - start_idx
        selected_day = st.selectbox("單元", unit_list, index=local_idx, label_visibility="collapsed")
        new_local_idx = unit_list.index(selected_day)
        if new_local_idx != local_idx:
            st.session_state.page_idx = start_idx + new_local_idx
            st.rerun()
            
    with c_speed:
        speed_options = {"正常 1.0x": 1.0, "微快 1.25x": 1.25, "衝刺 1.5x": 1.5, "超光速 2.0x": 2.0}
        selected_speed_label = st.selectbox("語速", list(speed_options.keys()), index=0, label_visibility="collapsed")
        play_speed = speed_options[selected_speed_label]
        
    with c_size:
        size_options = {
            "自動 (跨裝置適應)": "clamp(18px, 4vh, 50px)",
            "偏小 (手機專用)": "18px",
            "適中 (平板/電腦)": "24px",
            "偏大 (教室電視)": "36px",
            "特大 (巨無霸)": "48px"
        }
        selected_size_label = st.selectbox("字幕", list(size_options.keys()), index=0, label_visibility="collapsed")
        bubble_fs = size_options[selected_size_label]
    
    with c_prev:
        if st.button("⬅️"):
            st.session_state.page_idx = max(0, st.session_state.page_idx - 1)
            st.rerun()
    with c_next:
        if st.button("➡️"):
            st.session_state.page_idx = min(total_items - 1, st.session_state.page_idx + 1)
            st.rerun()

    main_container = st.empty()

# ==========================================
# 【編號 4】資料準備與解析
# ==========================================
    try:
        row = df.iloc[st.session_state.page_idx]
        try:
            pdf_page_idx = int(str(row['頁碼']).strip()) - 1
            if pdf_page_idx < 0: pdf_page_idx = 0
        except:
            pdf_page_idx = 0

        audio_path = str(row['Audio_Path']).strip().lstrip('/')
        audio_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path}?t={time.time()}"
        json_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path.replace('.mp3', '_script.json')}?t={time.time()}"
        
        pdf_b64 = get_pdf_page_as_base64("notes.pdf", pdf_page_idx)
        res_json = requests.get(json_url)
        script_data = res_json.text if res_json.status_code == 200 else "[]"

# ==========================================
# 【編號 5】HTML 骨架與 CSS 樣式
# ==========================================
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{ font-family: sans-serif; margin: 0; padding: 0; background: white; }}
            .header-bar {{ display: flex; align-items: center; justify-content: space-between; padding: clamp(5px, 1.5vh, 10px) 20px; border-bottom: 1px solid #f0f0f0; }}
            .title {{ color: #1d4ed8; font-size: clamp(20px, 3.5vw, 34px); font-weight: bold; margin: 0; }}
            
            .btn-group {{ display: flex; gap: 8px; }}
            .play-btn, .fs-btn {{ 
                background: linear-gradient(135deg, #2b58db, #1d4ed8); 
                color: white; padding: clamp(8px, 1.5vh, 10px) clamp(12px, 2vw, 25px); 
                border-radius: 50px; font-weight: bold; font-size: clamp(14px, 2vw, 18px); 
                cursor: pointer; border: none; transition: 0.3s ease; box-shadow: 0 4px 10px rgba(29, 78, 216, 0.2);
            }}
            .play-btn:hover, .fs-btn:hover {{ background: linear-gradient(135deg, #1e40af, #1d4ed8); box-shadow: 0 6px 15px rgba(29, 78, 216, 0.3); }}
            
            .pdf-view {{ position: relative; width: 100%; }}
            .pdf-img {{ width: 100%; display: block; }}
            
            .seek-panel {{ width: 100%; background: #fdfdfd; padding: 10px 20px; display: flex; align-items: center; gap: 15px; box-sizing: border-box; border-bottom: 1px solid #eee; }}
            input[type=range] {{ flex: 1; accent-color: #1d4ed8; cursor: pointer; height: 10px; }}
            .time-box {{ font-size: 14px; color: #64748b; min-width: 95px; text-align: right; }}
            
            .subtitle-stage {{ 
                position: absolute; bottom: 10%; width: 100%; display: flex; flex-direction: column; padding: 0 clamp(15px, 4vw, 40px); box-sizing: border-box; z-index: 10; pointer-events: none; 
            }}
            
            .bubble {{ 
                max-width: 90%; 
                padding: clamp(10px, 2.5vh, 30px); 
                border-radius: 20px; 
                box-shadow: 0 8px 30px rgba(0,0,0,0.08); 
                font-size: {bubble_fs}; 
                line-height: 1.5; 
                opacity: 0; 
                transition: all 0.3s ease; 
                backdrop-filter: blur(4px); 
                -webkit-backdrop-filter: blur(4px); 
                pointer-events: auto;
                font-weight: bold; 
            }}
            
            .yanjun {{ 
                align-self: flex-start; 
                background-color: rgba(227, 242, 253, 0.2); 
                color: #0d47a1; 
                border: 1px solid rgba(187, 222, 251, 0.5); 
                border-bottom-left-radius: 2px; 
            }}
            
            .xiaozhen {{ 
                align-self: flex-end; 
                background-color: rgba(254, 242, 242, 0.2); 
                color: #991b1b; 
                border: 1px solid rgba(254, 202, 202, 0.5); 
                border-bottom-right-radius: 2px; 
            }}
        </style>
        </head>
        <body>
            <div class="header-bar">
                <div class="title">🚀 考前60天衝刺</div>
                <div class="btn-group">
                    <button id="fsBtn" class="fs-btn">🔲 全螢幕</button>
                    <button id="pBtn" class="play-btn">▶️ 立刻收聽</button>
                </div>
            </div>
            <audio id="aud" src="{audio_url}" preload="auto"></audio>
            
            <div class="pdf-view">
                <img src="data:image/png;base64,{pdf_b64}" class="pdf-img">
                <div class="subtitle-stage">
                    <div id="bubble" class="bubble yanjun"><span id="msg"></span></div>
                </div>
            </div>
            
            <div class="seek-panel">
                <input type="range" id="sk" value="0" step="0.1">
                <div class="time-box"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
            </div>
            
            <script>
                const aud = document.getElementById('aud');
                const pBtn = document.getElementById('pBtn');
                const fsBtn = document.getElementById('fsBtn'); 
                const sk = document.getElementById('sk');
                const bubble = document.getElementById('bubble');
                const msg = document.getElementById('msg');
                const script = {script_data};
                
                aud.playbackRate = {play_speed};

                pBtn.onclick = () => {{
                    if(aud.paused) {{ aud.play(); pBtn.innerText = "⏸️ 暫停"; }}
                    else {{ aud.pause(); pBtn.innerText = "▶️ 繼續"; }}
                }};

                // 🌟 【全螢幕終極武裝版】：加入 WebKit 支援與防呆警示
                fsBtn.onclick = () => {{
                    const docElm = document.documentElement;
                    // 判斷目前是否為全螢幕狀態
                    if (!document.fullscreenElement && !document.webkitFullscreenElement) {{
                        if (docElm.requestFullscreen) {{
                            docElm.requestFullscreen().catch(err => {{
                                alert("【系統提示】您的手機瀏覽器安全機制阻擋了全螢幕功能！\\n\\n💡 替代戰術：請將手機「橫放」，雙指放大螢幕即可完美觀看！");
                            }});
                        }} else if (docElm.webkitRequestFullscreen) {{ /* Safari 與手機版 Chrome 支援 */
                            docElm.webkitRequestFullscreen();
                        }} else {{
                            alert("【系統提示】您的設備不支援網頁全螢幕功能，請將手機橫放觀看。");
                        }}
                        fsBtn.innerText = "✖️ 退出";
                    }} else {{
                        if (document.exitFullscreen) {{
                            document.exitFullscreen();
                        }} else if (document.webkitExitFullscreen) {{
                            document.webkitExitFullscreen();
                        }}
                        fsBtn.innerText = "🔲 全螢幕";
                    }}
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
                            let avatar = (s.speaker === '彥君') ? '👨‍🏫 ' : '👩‍🔬 ';
                            msg.innerText = avatar + s.text;
                            
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
        
# ==========================================
# 【編號 6】渲染區塊
# ==========================================
        with main_container:
            components.html(full_html, height=1400, scrolling=True)

    except Exception as e:
        st.error(f"系統錯誤：{e}")
else:
    st.error("Google Sheet 資料連線失敗。")
