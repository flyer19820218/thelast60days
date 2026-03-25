import streamlit as st
import pandas as pd
import requests
import fitz
import streamlit.components.v1 as components
import base64
import time
import math
import json

# ==========================================
# 【編號 1】頁面設定與 RWD 響應式 CSS (四格滿版 + 翩翩體)
# ==========================================
st.set_page_config(page_title="會考自然-ai教學", page_icon="📚", layout="wide")

st.markdown("""
    <style>
    /* 隱藏 Streamlit 預設介面 */
    #MainMenu, header, footer {visibility: hidden;}
    .stApp { background-color: #ffffff; }
    
    /* 🚀 呼叫蘋果內建「翩翩體」咒語 */
    html, body, [class*="css"], p, span, div, b, button, select, input {
        font-family: 'HanziPenTC-W5', 'HanziPenTC-W3', 'HanziPen TC', 'HanziPenSC-W5', 'HanziPenSC-W3', 'HanziPen SC', '翩翩體-繁', '翩翩體-簡', 'PingFang TC', 'Microsoft JhengHei', sans-serif !important;
    }
    
    .stSelectbox, .stNumberInput { margin-bottom: 0px !important; }
    
    .block-container {
        padding-top: 1rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        padding-bottom: 0rem !important;
        max-width: 100% !important;
    }
    
    /* 💡 強制鎖定手機版高度：讓下拉選單完美對齊 */
    div[data-baseweb="select"] { font-size: 16px !important; }
    div[data-baseweb="select"] > div { 
        height: 44px !important; 
        min-height: 44px !important; 
    }
    ul[data-baseweb="menu"] li { font-size: 16px !important; padding: 10px !important; }
    
    /* 🚀 全局隱藏 Python 端的 Streamlit 按鈕 */
    div[data-testid="stButton"] { 
        display: none !important; 
        height: 0px !important; 
        margin: 0px !important; 
        padding: 0px !important; 
    }

    /* 📺 大螢幕適配 (電腦/大電視) */
    @media (min-width: 1024px) {
        .block-container { padding-left: 2rem !important; padding-right: 2rem !important; } 
        div[data-baseweb="select"] { font-size: 24px !important; }
        
        div[data-baseweb="select"] > div { 
            height: 56px !important; 
            min-height: 56px !important; 
        }
        ul[data-baseweb="menu"] li { font-size: 22px !important; padding-top: 15px !important; padding-bottom: 15px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 【編號 2】資料讀取與 PDF 轉檔快取
# ==========================================
@st.cache_data(ttl=3600)
def load_data_fresh():
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
    try: return pd.read_csv(SHEET_URL)
    except: return None

@st.cache_data(show_spinner=False)
def get_pdf_page_as_base64(local_pdf_path, page_index):
    try:
        doc = fitz.open(local_pdf_path)
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)) 
        img_data = pix.tobytes("png")
        doc.close()
        return base64.b64encode(img_data).decode('utf-8')
    except: return ""

@st.cache_data(show_spinner=False)
def get_script_json(json_url):
    try:
        res = requests.get(json_url, timeout=5)
        if res.status_code == 200: return res.text
    except: pass
    return "[]"

# ==========================================
# 【編號 3】佈局實作 (完美純淨 4 格滿版)
# ==========================================
df = load_data_fresh()

if df is not None and not df.empty:
    if 'page_idx' not in st.session_state: st.session_state.page_idx = 0

    total_items = len(df)
    group_size = 10
    num_groups = math.ceil(total_items / group_size)
    group_labels = [f"進度 {i*group_size + 1} ~ {min((i+1)*group_size, total_items)}" for i in range(num_groups)]
    current_group_idx = st.session_state.page_idx // group_size

    # 🚀 上方控制列變成極度寬敞的「完美 4 欄」
    c_group, c_unit, c_speed, c_size = st.columns([1.5, 2.0, 1.0, 1.5])
    
    with c_group:
        selected_group = st.selectbox("範圍", group_labels, index=current_group_idx, label_visibility="collapsed")
        new_group_idx = group_labels.index(selected_group)
        if new_group_idx != current_group_idx:
            st.session_state.page_idx = new_group_idx * group_size
            st.rerun()

    with c_unit:
        start_idx = new_group_idx * group_size
        end_idx = min(start_idx + group_size, total_items)
        unit_list = df.iloc[start_idx:end_idx]['Title'].tolist()
        local_idx = st.session_state.page_idx - start_idx
        selected_day = st.selectbox("單元", unit_list, index=local_idx, label_visibility="collapsed")
        new_local_idx = unit_list.index(selected_day)
        if new_local_idx != local_idx:
            st.session_state.page_idx = start_idx + new_local_idx
            st.rerun()
            
    with c_speed:
        speed_options = {"正常 1.0x": 1.0, "微快 1.25x": 1.25, "衝刺 1.5x": 1.5, "超光速 2.0x": 2.0}
        play_speed = speed_options[st.selectbox("語速", list(speed_options.keys()), index=0, label_visibility="collapsed")]
        
    with c_size:
        size_options = {
            "自動適配螢幕 (佳)": "clamp(20px, 4vw, 70px)", 
            "80吋電視霸氣 (大)": "clamp(32px, 5vw, 100px)",
            "電腦標準教學 (中)": "clamp(24px, 3.5vw, 65px)",
            "手機專用小螢幕 (小)": "clamp(18px, 5vmin, 36px)"
            
        }
        bubble_fs = size_options[st.selectbox("字幕大小", list(size_options.keys()), index=0, label_visibility="collapsed")]

    # 👻 幽靈按鈕：純給 JavaScript 自動點擊換頁用的
    if st.button("AutoNextHiddenBtn", key="hidden_next"):
        if st.session_state.page_idx < total_items - 1:
            st.session_state.page_idx += 1
            st.rerun()

    main_container = st.empty()

# ==========================================
# 【編號 4】資料準備與解析
# ==========================================
    try:
        row = df.iloc[st.session_state.page_idx]
        pdf_page_idx = int(str(row['頁碼']).strip()) - 1 if '頁碼' in df.columns else 0
        audio_path = str(row['Audio_Path']).strip().lstrip('/')
        audio_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path}?t={time.time()}"
        json_url = f"https://raw.githubusercontent.com/flyer19820218/thelast60days/main/{audio_path.replace('.mp3', '_script.json')}"
        
        pdf_b64 = get_pdf_page_as_base64("notes.pdf", max(0, pdf_page_idx))
        
        script_data = get_script_json(json_url)
        safe_script_data = json.dumps(script_data)

# ==========================================
# 【編號 5】HTML 骨架與 CSS 樣式
# ==========================================
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
        <script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
        
        <style>
            body {{ 
                font-family: 'HanziPenTC-W5', 'HanziPenTC-W3', 'HanziPen TC', 'HanziPenSC-W5', 'HanziPenSC-W3', 'HanziPen SC', '翩翩體-繁', '翩翩體-簡', 'PingFang TC', 'Microsoft JhengHei', sans-serif; 
                margin: 0; padding: 0; background: white; transition: background 0.3s; 
            }}
            
            .header-bar {{ display: flex; align-items: center; justify-content: space-between; padding: clamp(5px, 1.5vh, 10px) 20px; border-bottom: 1px solid #f0f0f0; transition: 0.3s; }}
            .title {{ color: #1d4ed8; font-size: clamp(20px, 3.5vw, 34px); font-weight: bold; margin: 0; }}
            
            .btn-group {{ display: flex; gap: 8px; }}
            .play-btn {{ 
                background: linear-gradient(135deg, #2b58db, #1d4ed8); color: white; padding: clamp(8px, 1.5vh, 10px) clamp(12px, 2vw, 25px); 
                border-radius: 50px; font-weight: bold; font-size: clamp(14px, 2vw, 18px); cursor: pointer; border: none; box-shadow: 0 4px 10px rgba(29, 78, 216, 0.2);
                font-family: inherit; transition: all 0.3s ease;
            }}
            .play-btn:hover {{ background: linear-gradient(135deg, #1e40af, #1d4ed8); box-shadow: 0 6px 15px rgba(29, 78, 216, 0.3); }}
            
            .pdf-view {{ position: relative; width: 100%; overflow: hidden; }}
            .pdf-img {{ width: 100%; display: block; }}
            
            .seek-panel {{ width: 100%; background: #fdfdfd; padding: 10px 20px; display: flex; align-items: center; gap: 15px; box-sizing: border-box; border-bottom: 1px solid #eee; }}
            input[type=range] {{ flex: 1; accent-color: #1d4ed8; cursor: pointer; height: 10px; }}
            .time-box {{ font-size: 14px; color: #64748b; min-width: 95px; text-align: right; }}
            
            .subtitle-stage {{ position: absolute; bottom: 8%; width: 100%; display: flex; flex-direction: column; padding: 0 clamp(15px, 4vw, 40px); box-sizing: border-box; z-index: 10; pointer-events: none; }}
            .bubble {{ 
                max-width: 90%; padding: clamp(10px, 2.5vmin, 30px); border-radius: 20px; box-shadow: 0 8px 30px rgba(0,0,0,0.08); 
                font-size: {bubble_fs}; line-height: 1.5; opacity: 0; transition: all 0.1s ease; font-weight: bold; 
            }}
            
            .yanjun {{ align-self: flex-start; background-color: rgba(227, 242, 253, 0.95); color: #0d47a1; border: 1px solid rgba(187, 222, 251, 0.5); border-bottom-left-radius: 2px; }}
            .xiaozhen {{ align-self: flex-end; background-color: rgba(254, 242, 242, 0.95); color: #991b1b; border: 1px solid rgba(254, 202, 202, 0.5); border-bottom-right-radius: 2px; }}
            .chorus {{ align-self: center; background: linear-gradient(135deg, #fff9c4 0%, #fde68a 100%); color: #92400e; border: 1px solid #f59e0b; border-radius: 20px; text-align: center; }}

            /* 🎯 釘選黑板區塊 */
            .board-stage {{
                position: absolute; bottom: calc(8% + {bubble_fs} * 2.8); width: 100%; display: flex; flex-direction: column; gap: 8px;
                padding: 0 clamp(15px, 4vw, 40px); box-sizing: border-box; z-index: 5; pointer-events: none;
            }}
            .board-item {{
                align-self: flex-start; background-color: rgba(240, 248, 255, 0.95); color: #0d47a1;
                padding: clamp(8px, 1.5vmin, 20px) clamp(15px, 2.5vmin, 30px); border-radius: 12px;
                font-size: calc({bubble_fs} * 0.9); font-weight: bold; border-left: 5px solid #1d4ed8; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                margin-left: calc(clamp(10px, 2.5vmin, 30px) + {bubble_fs} * 1.6);
            }}

            @media (max-width: 768px) {{
                .subtitle-stage {{ bottom: 3% !important; padding: 0 10px !important; }}
                .board-stage {{ bottom: calc(3% + {bubble_fs} * 3) !important; padding: 0 10px !important; }}
                .bubble {{ padding: 8px 12px !important; border-radius: 12px !important; max-width: 95% !important; }}
                .board-item {{ margin-left: calc(8px + {bubble_fs} * 1.4) !important; padding: 6px 12px !important; }}
            }}

            body.theater {{ background-color: #000; }}
            body.theater .header-bar, body.theater .seek-panel {{ background-color: #111; border: none; }}
            body.theater .title, body.theater .time-box {{ color: #ccc; }}
        </style>
        </head>
        <body>
            <div class="header-bar">
                <div class="title">🚀 考前60天衝刺</div>
                <div class="btn-group">
                    <button id="autoPlayBtn" class="play-btn">▶️ 開啟連播</button>
                    <button id="fsBtn" class="play-btn">🔲 全螢幕</button>
                    <button id="pBtn" class="play-btn">▶️ 立刻收聽</button>
                </div>
            </div>
            <audio id="aud" src="{audio_url}" preload="auto"></audio>
            
            <div class="pdf-view">
                <img src="data:image/png;base64,{pdf_b64}" class="pdf-img">
                <div id="board-stage" class="board-stage"></div>
                <div class="subtitle-stage"><div id="bubble" class="bubble"><span id="msg"></span></div></div>
            </div>
            
            <div class="seek-panel">
                <input type="range" id="sk" value="0" step="0.1">
                <div class="time-box"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
            </div>
            
            <script>
                const aud = document.getElementById('aud');
                const pBtn = document.getElementById('pBtn');
                const fsBtn = document.getElementById('fsBtn'); 
                const autoPlayBtn = document.getElementById('autoPlayBtn');
                const sk = document.getElementById('sk');
                const boardStage = document.getElementById('board-stage');
                const bubble = document.getElementById('bubble');
                const msg = document.getElementById('msg');
                
                // 🚀 JS 記憶黑科技：跨越換頁記住連播狀態
                let isAutoPlay = false;
                try {{ isAutoPlay = localStorage.getItem('yt_autoplay') === 'true'; }} catch(e) {{}}
                
                function updateAutoPlayUI() {{
                    if(isAutoPlay) {{
                        autoPlayBtn.innerText = "🔄 正在連播";
                        autoPlayBtn.style.background = "linear-gradient(135deg, #1d4ed8, #1e40af)"; 
                    }} else {{
                        autoPlayBtn.innerText = "▶️ 開啟連播";
                        autoPlayBtn.style.background = ""; 
                    }}
                }}
                updateAutoPlayUI();

                autoPlayBtn.onclick = () => {{
                    isAutoPlay = !isAutoPlay;
                    try {{ localStorage.setItem('yt_autoplay', isAutoPlay); }} catch(e) {{}}
                    updateAutoPlayUI();
                }};
                
                const scriptRaw = {safe_script_data};
                let script = [];
                try {{ script = JSON.parse(scriptRaw); }} catch(e) {{ console.error("Script parse error"); }}
                
                let lastMsgHash = ""; 
                aud.playbackRate = {play_speed};

                if (isAutoPlay) {{
                    setTimeout(() => {{
                        aud.play().then(() => {{
                            pBtn.innerText = "⏸️ 暫停";
                        }}).catch(e => console.log("瀏覽器阻擋自動播放"));
                    }}, 500);
                }}

                pBtn.onclick = () => {{ if(aud.paused) {{ aud.play(); pBtn.innerText = "⏸️ 暫停"; }} else {{ aud.pause(); pBtn.innerText = "▶️ 繼續"; }} }};
                fsBtn.onclick = () => {{
                    if (!document.fullscreenElement) {{ document.documentElement.requestFullscreen(); document.body.classList.add('theater'); }}
                    else {{ document.exitFullscreen(); document.body.classList.remove('theater'); }}
                }};

                aud.onloadedmetadata = () => {{ document.getElementById('dur').innerText = fmt(aud.duration); sk.max = aud.duration; }};
                
                // 🌟 新增一個強大的 LaTeX 解析函數
                function renderTextWithMath(text) {{
                    let html = text.replace(/\$\$([^\$]+)\$\$/g, function(match, mathCode) {{
                        try {{ return katex.renderToString(mathCode, {{displayMode: true, throwOnError: false}}); }}
                        catch(e) {{ return match; }}
                    }});
                    html = html.replace(/\$([^\$]+)\$/g, function(match, mathCode) {{
                        try {{ return katex.renderToString(mathCode, {{displayMode: false, throwOnError: false}}); }}
                        catch(e) {{ return match; }}
                    }});
                    return html;
                }}

                aud.ontimeupdate = () => {{
                    const t = aud.currentTime;
                    document.getElementById('cur').innerText = fmt(t);
                    sk.value = t;
                    
                    let mainSub = null;
                    let activePins = [];
                    
                    for(let s of script) {{
                        if(t >= s.start && t <= s.end) {{
                            if(s.is_pinned) activePins.push(s); else mainSub = s;
                        }}
                    }}

                    // 🎯 處理主字幕 (✨ V20 語音同步動態打字機版 ✨)
                    if (mainSub) {{
                        let avatar = mainSub.speaker === '彥君' ? '👨‍🏫 ' : (mainSub.speaker === '曉臻' ? '👩‍🔬 ' : '🎙️ ');
                        let bClass = mainSub.speaker === '彥君' ? 'yanjun' : (mainSub.speaker === '曉臻' ? 'xiaozhen' : 'chorus');
                        let rawText = avatar + mainSub.text;
                        
                        // 檢查這句話有沒有包含 LaTeX 公式符號 '$'
                        let hasMath = rawText.includes('$');

                        if (hasMath) {{
                            // 🛡️ 保護模式：有公式，直接整句渲染，不套用打字機
                            if (lastMsgHash !== rawText) {{
                                msg.innerHTML = renderTextWithMath(rawText);
                                bubble.className = "bubble " + bClass;
                                bubble.style.opacity = 1;
                                lastMsgHash = rawText;
                            }}
                        }} else {{
                            // 🚀 打字機模式：計算語音進度百分比
                            let duration = mainSub.end - mainSub.start;
                            if (duration <= 0) duration = 0.1; // 預防除以0
                            
                            let progress = (t - mainSub.start) / duration;
                            if (progress < 0) progress = 0;
                            if (progress > 1) progress = 1;
                            
                            // 依照進度，算出現在該顯示幾個字
                            let charsToShow = Math.floor(progress * rawText.length);
                            
                            // 保底讓大頭貼先顯示出來
                            if (charsToShow < avatar.length) charsToShow = avatar.length;
                            
                            msg.innerHTML = rawText.substring(0, charsToShow);
                            bubble.className = "bubble " + bClass;
                            bubble.style.opacity = 1;
                            lastMsgHash = "typing..."; // 標記打字中，不鎖定 hash
                        }}
                    }} else {{
                        if (lastMsgHash !== "") {{ bubble.style.opacity = 0; lastMsgHash = ""; }}
                    }}

                    // 🎯 處理釘選黑板
                    activePins.forEach(pin => {{
                        const pinId = 'pin-' + Math.floor(pin.start * 10);
                        if (!document.getElementById(pinId)) {{
                            const d = document.createElement('div');
                            d.id = pinId;
                            d.className = 'board-item';
                            d.innerHTML = renderTextWithMath(pin.text);
                            boardStage.appendChild(d);
                        }}
                    }});

                    Array.from(boardStage.children).forEach(child => {{
                        if (!activePins.some(p => 'pin-' + Math.floor(p.start * 10) === child.id)) boardStage.removeChild(child);
                    }});
                }};
                
                aud.onended = () => {{
                    if (isAutoPlay) {{
                        const parentBtns = window.parent.document.querySelectorAll('button');
                        for (let btn of parentBtns) {{
                            if (btn.innerText.includes('AutoNextHiddenBtn')) {{
                                btn.click();
                                break;
                            }}
                        }}
                    }}
                }};

                sk.oninput = () => aud.currentTime = sk.value;
                function fmt(s) {{ return Math.floor(s/60) + ":" + String(Math.floor(s%60)).padStart(2,'0'); }}
            </script>
        </body>
        </html>
        """
# ==========================================
# 【編號 6】前端渲染區塊
# ==========================================
        with main_container: components.html(full_html, height=1400, scrolling=True)

    except Exception as e: st.error(f"系統錯誤： {e}")
else: st.error("資料連線失敗。")
