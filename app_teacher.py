# 1. 先注入樣式 (保持置底 YouTube 質感)
st.markdown("""
<style>
    .header-bar { position: fixed; top: 0; width: 100%; z-index: 100; display: flex; align-items: center; justify-content: space-between; padding: 10px 20px; background: rgba(255,255,255,0.9); box-shadow: 0 2px 10px rgba(0,0,0,0.3); }
    .title { color: #1d4ed8; font-size: 24px; font-weight: bold; margin: 0; }
    .play-btn { background: #ff0000; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold; cursor: pointer; border: none; }
    .pdf-container { margin-top: 60px; margin-bottom: 150px; width: 100%; }
    .pdf-img { width: 100%; display: block; }
    .bottom-console { position: fixed; bottom: 0; width: 100%; background: rgba(0, 0, 0, 0.9); color: white; padding: 15px 0; z-index: 100; display: flex; flex-direction: column; align-items: center; min-height: 120px; }
    .seek-panel { width: 90%; display: flex; align-items: center; gap: 15px; margin-bottom: 10px; }
    input[type=range] { flex: 1; accent-color: #ff0000; cursor: pointer; }
    .subtitle-text { font-size: 32px; font-weight: bold; text-align: center; min-height: 50px; text-shadow: 2px 2px 4px rgba(0,0,0,1); padding: 0 20px; line-height: 1.4; }
    .speaker-label { font-size: 18px; color: #ffff00; margin-bottom: 5px; font-weight: bold; }
    .highlight { color: #ffff00; }
</style>
""", unsafe_allow_html=True)

# 2. 定義 HTML 模板 (使用 @變數@ 避開大括號衝突)
html_template = """
<!DOCTYPE html>
<html>
<body>
    <div class="header-bar">
        <div class="title">🎬 考前60天衝刺：@TITLE@</div>
        <button id="pBtn" class="play-btn">▶️ 播放影片</button>
    </div>
    <audio id="aud" src="@AUDIO_URL@" preload="auto"></audio>
    <div class="pdf-container">
        <img src="data:image/png;base64,@PDF_B64@" class="pdf-img">
    </div>
    <div class="bottom-console">
        <div class="seek-panel">
            <input type="range" id="sk" value="0" step="0.1">
            <div style="font-size:14px;"><span id="cur">0:00</span> / <span id="dur">0:00</span></div>
        </div>
        <div id="spk" class="speaker-label"></div>
        <div id="msg" class="subtitle-text"></div>
    </div>
    <script>
        const aud = document.getElementById('aud');
        const pBtn = document.getElementById('pBtn');
        const sk = document.getElementById('sk');
        const spk = document.getElementById('spk');
        const msg = document.getElementById('msg');
        const script = @SCRIPT_DATA@;
        
        aud.playbackRate = @PLAY_SPEED@;

        pBtn.onclick = () => {
            if(aud.paused) { aud.play(); pBtn.innerText = "⏸ 暫停"; }
            else { aud.pause(); pBtn.innerText = "▶ 繼續"; }
        };
        aud.onloadedmetadata = () => {
            document.getElementById('dur').innerText = fmt(aud.duration);
            sk.max = aud.duration;
        };
        aud.ontimeupdate = () => {
            const t = aud.currentTime;
            document.getElementById('cur').innerText = fmt(t);
            sk.value = t;
            let hit = false;
            for(let s of script) {
                if(t >= s.start && t <= s.end) {
                    spk.innerText = (s.speaker === '彥君' ? '👨‍🏫 彥君老師' : '👩‍🔬 曉臻助教');
                    let processedText = s.text.replace(/『/g, '<span class="highlight">').replace(/』/g, '</span>');
                    msg.innerHTML = processedText;
                    hit = true; break;
                }
            }
            if(!hit) { msg.innerText = ""; spk.innerText = ""; }
        };
        sk.oninput = () => aud.currentTime = sk.value;
        function fmt(s) { return Math.floor(s/60) + ":" + String(Math.floor(s%60)).padStart(2,'0'); }
    </script>
</body>
</html>
"""

# 3. 執行最終替換 (戰士這招最穩！)
full_html = html_template.replace("@TITLE@", row['Title']) \
                         .replace("@AUDIO_URL@", audio_url) \
                         .replace("@PDF_B64@", pdf_b64) \
                         .replace("@SCRIPT_DATA@", script_data) \
                         .replace("@PLAY_SPEED@", str(play_speed))

# 4. 渲染頁面
with main_container:
    components.html(full_html, height=1800, scrolling=True)
