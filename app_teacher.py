# ==========================================
# 調整後的 HTML/CSS (YouTuber 置底字幕版)
# ==========================================

full_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{ 
        font-family: 'Microsoft JhengHei', sans-serif; 
        margin: 0; 
        padding: 0; 
        background: #1a1a1a; /* 深色背景更有電影感 */
        overflow-x: hidden;
    }}
    /* 頂部導覽列 */
    .header-bar {{ 
        position: fixed; top: 0; width: 100%; z-index: 100;
        display: flex; align-items: center; justify-content: space-between; 
        padding: 10px 20px; background: rgba(255,255,255,0.9); 
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }}
    .title {{ color: #1d4ed8; font-size: 24px; font-weight: bold; margin: 0; }}
    .play-btn {{ 
        background: #ff0000; color: white; padding: 8px 20px; 
        border-radius: 5px; font-weight: bold; cursor: pointer; border: none; 
    }}

    /* PDF 主視區 */
    .pdf-container {{ 
        margin-top: 60px; 
        margin-bottom: 120px; /* 預留給置底字幕的空間 */
        width: 100%; 
    }}
    .pdf-img {{ width: 100%; display: block; }}

    /* 置底控制與字幕區 */
    .bottom-console {{
        position: fixed; bottom: 0; width: 100%; 
        background: rgba(0, 0, 0, 0.85); /* 半透明黑 */
        color: white; padding: 15px 0; z-index: 100;
        display: flex; flex-direction: column; align-items: center;
    }}
    .seek-panel {{ 
        width: 90%; display: flex; align-items: center; gap: 15px; margin-bottom: 10px;
    }}
    input[type=range] {{ flex: 1; accent-color: #ff0000; cursor: pointer; }}

    /* YouTube 標誌性字幕 */
    .subtitle-text {{
        font-size: 28px; /* 學校電視建議大字 */
        font-weight: bold;
        text-align: center;
        min-height: 40px;
        text-shadow: 2px 2px 4px rgba(0,0,0,1);
        padding: 0 20px;
        line-height: 1.4;
    }}
    .speaker-label {{
        font-size: 16px; color: #aaaaaa; margin-bottom: 5px;
    }}
    /* 關鍵字亮黃色 (腳本內有 『』 時 JS 會處理) */
    .highlight {{ color: #ffff00; }} 
</style>
</head>
<body>
    <div class="header-bar">
        <div class="title">🎬 考前60天衝刺：{row['Title']}</div>
        <button id="pBtn" class="play-btn">▶️立刻收聽</button>
    </div>

    <audio id="aud" src="{audio_url}" preload="auto"></audio>

    <div class="pdf-container">
        <img src="data:image/png;base64,{pdf_b64}" class="pdf-img">
    </div>

    <div class="bottom-console">
        <div class="seek-panel">
            <input type="range" id="sk" value="0" step="0.1">
            <div style="font-size:12px;"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
        </div>
        <div id="spk" class="speaker-label"></div>
        <div id="msg" class="subtitle-text">準備開始...</div>
    </div>

    <script>
        const aud = document.getElementById('aud');
        const pBtn = document.getElementById('pBtn');
        const sk = document.getElementById('sk');
        const spk = document.getElementById('spk');
        const msg = document.getElementById('msg');
        const script = {script_data};
        
        aud.playbackRate = {play_speed};

        pBtn.onclick = () => {{
            if(aud.paused) {{ aud.play(); pBtn.innerText = "⏸ 暫停"; }}
            else {{ aud.pause(); pBtn.innerText = "▶ 繼續"; }}
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
                    spk.innerText = (s.speaker === '彥君' ? '【 彥君老師 】' : '【 曉臻助教 】');
                    // 將腳本中的 『 』 轉換為亮黃色 span
                    let processedText = s.text.replace(/『/g, '<span class="highlight">').replace(/』/g, '</span>');
                    msg.innerHTML = processedText;
                    hit = true; break;
                }}
            }}
            if(!hit) {{ msg.innerText = ""; spk.innerText = ""; }}
        }};

        sk.oninput = () => aud.currentTime = sk.value;
        function fmt(s) {{ return Math.floor(s/60) + ":" + String(Math.floor(s%60)).padStart(2,'0'); }}
    </script>
</body>
</html>
"""
