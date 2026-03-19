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
st.set_page_config(page_title="會考自然-旗艦教學版", page_icon="📚", layout="wide")

st.markdown("""
    <style>
    /* 隱藏 Streamlit 預設介面 */
    #MainMenu, header, footer {visibility: hidden;}
    .stApp { background-color: #ffffff; }
    html, body, [class*="css"], p, span, div, b {
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
    }
    .stSelectbox, .stNumberInput { margin-bottom: 0px !important; }
    
    /* 🌟 移除 Streamlit 邊距， 讓畫面貼齊螢幕邊緣 */
    .block-container {
        padding-top: 1rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        padding-bottom: 0rem !important;
        max-width: 100% !important;
    }
    
    /* 📱【手機/平板預設模式】 */
    div[data-baseweb="select"] { font-size: 16px !important; }
    div[data-baseweb="select"] > div { min-height: 40px !important; }
    ul[data-baseweb="menu"] li { font-size: 16px !important; padding: 10px !important; }
    .stButton > button { font-size: 16px !important; min-height: 40px !important; width: 100% !important; padding: 5px !important; }
    
    /* 📺【大電視霸氣模式】 */
    @media (min-width: 1024px) {
        .block-container { padding-left: 2rem !important; padding-right: 2rem !important; } 
        div[data-baseweb="select"] { font-size: 24px !important; }
        div[data-baseweb="select"] > div { min-height: 55px !important; }
        ul[data-baseweb="menu"] li { font-size: 22px !important; padding-top: 15px !important; padding-bottom: 15px !important; }
        .stButton > button { font-size: 24px !important; min-height: 55px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 【編號 2】資料讀取與 PDF 轉檔 (加入加速快取)
# ==========================================
@st.cache_data(ttl=3600)
def load_data_fresh():
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
    try:
        return pd.read_csv(SHEET_URL)
    except:
        return None

@st.cache_data(show_spinner=False)
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

@st.cache_data(show_spinner=False)
def get_script_json(json_url):
    try:
        res = requests.get(json_url, timeout=5)
        if res.status_code == 200:
            return res.text
    except:
        pass
    return "[]"

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

    c_group, c_unit, c_speed, c_size = st.columns([1.5, 1.7, 1.0, 1.8])
    
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
            "電視霸氣 (後排看清楚)": "clamp(32px, 5vw, 100px)",
            "標準教學 (大螢幕首選)": "clamp(24px, 3.5vw, 65px)",
            "手機隨身 (近距離讀)": "clamp(18px, 5vmin, 36px)",
            "自動適配 (系統計算)": "clamp(20px, 4vw, 70px)" 
        }
        selected_size_label = st.selectbox("字幕大小", list(size_options.keys()), index=0, label_visibility="collapsed")
        bubble_fs = size_options[selected_size_label]

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
        json_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path.replace('.mp3', '_script.json')}"
        
        pdf_b64 = get_pdf_page_as_base64("notes.pdf", pdf_page_idx)
        script_data = get_script_json(json_url)

# ==========================================
# 【編號 5】HTML 骨架與 CSS 樣式 (升級版)
# ==========================================
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
        <script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
        
        <style>
            body {{ font-family: sans-serif; margin: 0; padding: 0; background: white; transition: background 0.3s; }}
            .header-bar {{ display: flex; align-items: center; justify-content: space-between; padding: clamp(5px, 1.5vh, 10px) 20px; border-bottom: 1px solid #f0f0f0; transition: 0.3s; }}
            .title {{ color: #1d4ed8; font-size: clamp(20px, 3.5vw, 34px); font-weight: bold; margin: 0; transition: 0.3s; }}
            
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
            
            .seek-panel {{ width: 100%; background: #fdfdfd; padding: 10px 20px; display: flex; align-items: center; gap: 15px; box-sizing: border-box; border-bottom: 1px solid #eee; transition: 0.3s; }}
            input[type=range] {{ flex: 1; accent-color: #1d4ed8; cursor: pointer; height: 10px; }}
            .time-box {{ font-size: 14px; color: #64748b; min-width: 95px; text-align: right; }}
            
            /* 💬 對話區設定 */
            .subtitle-stage {{ 
                position: absolute; bottom: 8%; width: 100%; display: flex; flex-direction: column; padding: 0 clamp(15px, 4vw, 40px); box-sizing: border-box; z-index: 10; pointer-events: none; 
            }}
            
            .bubble {{ 
                max-width: 90%; 
                padding: clamp(10px, 2.5vmin, 30px); 
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
            
            .yanjun {{ align-self: flex-start; background-color: rgba(227, 242, 253, 0.95); color: #0d47a1; border: 1px solid rgba(187, 222, 251, 0.5); border-bottom-left-radius: 2px; }}
            .xiaozhen {{ align-self: flex-end; background-color: rgba(254, 242, 242, 0.95); color: #991b1b; border: 1px solid rgba(254, 202, 202, 0.5); border-bottom-right-radius: 2px; }}
            .chorus {{ align-self: center; background: linear-gradient(135deg, #fff9c4 0%, #fde68a 100%); color: #92400e; border: 1px solid #f59e0b; border-radius: 20px; text-align: center; box-shadow: 0 4px 12px rgba(251, 191, 36, 0.4); }}

            /* 📌 算式板書區設定 (動態靠左對齊) */
            .board-stage {{
                position: absolute; 
                bottom: calc(8% + {bubble_fs} * 2.8); /* 動態疊在對話框上方 */
                width: 100%;
                display: flex; flex-direction: column; gap: 8px;
                padding: 0 clamp(15px, 4vw, 40px); /* 和對話區相同的左右邊距 */
                box-sizing: border-box; z-index: 5; pointer-events: none;
            }}
            
            .board-item {{
                align-self: flex-start; /* 永遠靠左，跟彥君同側 */
                background-color: rgba(240, 248, 255, 0.95); /* 和彥君氣泡相近的淺藍底色 */
                color: #0d47a1;
                padding: clamp(8px, 1.5vmin, 20px) clamp(15px, 2.5vmin, 30px);
                border-radius: 12px;
                font-size: calc({bubble_fs} * 0.9);
                font-weight: bold;
                border-left: 5px solid #1d4ed8;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                /* 🚀 核心排版魔法：往右推移，扣掉對話框的 padding 和頭像寬度，讓文字在同一條垂直線上！ */
                margin-left: calc(clamp(10px, 2.5vmin, 30px) + {bubble_fs} * 1.6);
                animation: fadeIn 0.4s ease-out forwards;
            }}

            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}

            @media (max-width: 768px) {{
                .subtitle-stage {{ bottom: 3% !important; padding: 0 10px !important; }}
                .board-stage {{ bottom: calc(3% + {bubble_fs} * 3) !important; padding: 0 10px !important; }}
                .bubble {{ padding: 8px 12px !important; border-radius: 12px !important; max-width: 95% !important; }}
                /* 手機版頭像較小，推移量微調 */
                .board-item {{ margin-left: calc(8px + {bubble_fs} * 1.4) !important; padding: 6px 12px !important; }}
            }}

            body.theater {{ background-color: #000; }}
            body.theater .header-bar {{ background-color: #111; border-bottom: 1px solid #333; }}
            body.theater .title {{ color: #ccc; }}
            body.theater .seek-panel {{ background-color: #111; border-bottom: none; border-top: 1px solid #333; }}
            body.theater .time-box {{ color: #aaa; }}
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
                <div id="board-stage" class="board-stage"></div>
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
                const boardStage = document.getElementById('board-stage');
                const bubble = document.getElementById('bubble');
                const msg = document.getElementById('msg');
                const script = {script_data};
                
                let lastMsgHash = ""; // 防閃爍鎖定器

                aud.playbackRate = {play_speed};

                pBtn.onclick = () => {{
                    if(aud.paused) {{ aud.play(); pBtn.innerText = "⏸️ 暫停"; }}
                    else {{ aud.pause(); pBtn.innerText = "▶️ 繼續"; }}
                }};

                let isTheater = false;
                fsBtn.onclick = () => {{
                    const docElm = document.documentElement;
                    
                    if (!document.fullscreenElement && !document.webkitFullscreenElement && !isTheater) {{
                        let req = docElm.requestFullscreen || docElm.webkitRequestFullscreen;
                        if (req) {{
                            let promise = req.call(docElm);
                            if (promise) {{
                                promise.catch(err => {{ enableTheater(); }});
                            }} else {{
                                setTimeout(() => {{
                                    if (!document.fullscreenElement && !document.webkitFullscreenElement) enableTheater();
                                }}, 200);
                            }}
                        }} else {{
                            enableTheater();
                        }}
                    }} else {{
                        if (document.exitFullscreen && document.fullscreenElement) document.exitFullscreen();
                        else if (document.webkitExitFullscreen && document.webkitFullscreenElement) document.webkitExitFullscreen();
                        disableTheater();
                    }}
                }};

                function enableTheater() {{
                    isTheater = true;
                    document.body.classList.add('theater');
                    fsBtn.innerText = "✖️ 退出劇院";
                    
                    let toast = document.createElement('div');
                    toast.id = 'ios-toast';
                    toast.style.cssText = "position:absolute; top:30%; left:50%; transform:translateX(-50%); background:rgba(0,100,255,0.9); color:white; padding:15px 25px; border-radius:10px; font-size:18px; z-index:9999; text-align:center; font-weight:bold; box-shadow:0 10px 30px rgba(0,0,0,0.5); width: 80%; max-width: 300px;";
                    toast.innerHTML = "📱 已啟動【劇院模式】<br><span style='font-size:14px; font-weight:normal;'>蘋果設備請將手機轉為「橫向」觀看</span>";
                    document.querySelector('.pdf-view').appendChild(toast);
                    
                    setTimeout(() => {{ if(document.getElementById('ios-toast')) document.getElementById('ios-toast').remove(); }}, 3500);
                }}

                function disableTheater() {{
                    isTheater = false;
                    document.body.classList.remove('theater');
                    fsBtn.innerText = "🔲 全螢幕";
                    if(document.getElementById('ios-toast')) document.getElementById('ios-toast').remove();
                }}

                aud.onloadedmetadata = () => {{
                    document.getElementById('dur').innerText = fmt(aud.duration);
                    sk.max = aud.duration;
                }};
                
                // 🚀 核心升級：雙軌解析與 DOM 差異化更新
                aud.ontimeupdate = () => {{
                    const t = aud.currentTime;
                    document.getElementById('cur').innerText = fmt(t);
                    sk.value = t;
                    
                    let mainSub = null;
                    let activePins = [];
                    
                    // 1. 分流掃描
                    for(let s of script) {{
                        if(t >= s.start && t <= s.end) {{
                            if(s.is_pinned) activePins.push(s);
                            else mainSub = s;
                        }}
                    }}

                    // 2. 💬 一般對話泡泡更新 (防閃爍)
                    if (mainSub) {{
                        let avatar = mainSub.speaker === '彥君' ? '👨‍🏫 ' : (mainSub.speaker === '曉臻' ? '👩‍🔬 ' : '🎙️ ');
                        let bClass = mainSub.speaker === '彥君' ? 'yanjun' : (mainSub.speaker === '曉臻' ? 'xiaozhen' : 'chorus');
                        let currentHash = avatar + mainSub.text;
                        
                        if (lastMsgHash !== currentHash) {{
                            let rawText = avatar + mainSub.text;
                            // 如果有反斜線，觸發 LaTeX 渲染
                            if (rawText.includes('\\\\')) {{
                                try {{ msg.innerHTML = katex.renderToString(rawText, {{throwOnError: false}}); }}
                                catch(e) {{ msg.innerText = rawText; }}
                            }} else {{
                                msg.innerText = rawText;
                            }}
                            bubble.className = "bubble " + bClass;
                            bubble.style.opacity = 1;
                            lastMsgHash = currentHash;
                        }}
                    }} else {{
                        if (lastMsgHash !== "") {{ bubble.style.opacity = 0; lastMsgHash = ""; }}
                    }}

                    // 3. 📌 黑板算式更新 (DOM 差異化新增/移除，絕對防閃)
                    // A. 加入新算式
                    activePins.forEach(pin => {{
                        const pinId = 'pin-' + Math.floor(pin.start * 10);
                        if (!document.getElementById(pinId)) {{
                            const d = document.createElement('div');
                            d.id = pinId;
                            d.className = 'board-item';
                            try {{
                                d.innerHTML = katex.renderToString(pin.text, {{ throwOnError: false }});
                            }} catch(e) {{ 
                                d.innerText = pin.text; 
                            }}
                            boardStage.appendChild(d);
                        }}
                    }});

                    // B. 移除已過期或回放時的舊算式
                    Array.from(boardStage.children).forEach(child => {{
                        const stillActive = activePins.some(p => 'pin-' + Math.floor(p.start * 10) === child.id);
                        if (!stillActive) {{
                            boardStage.removeChild(child);
                        }}
                    }});
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
        st.error(f"系統錯誤： {e}")
else:
    st.error("Google Sheet 資料連線失敗。")
