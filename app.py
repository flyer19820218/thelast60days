import streamlit as st
import time
import base64

# --- 1. 頁面設定 (強制手機視覺寬度) ---
st.set_page_config(page_title="自然科學的真理 PODCAST", layout="centered")

# 自定義 CSS：讓介面更像手機 App，並美化播放器
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #4CAF50; color: white; }
    .podcast-container { background-color: white; padding: 20px; border-radius: 15px; shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    .typing-text { font-family: 'Courier New', Courier, monospace; line-height: 1.6; color: #333; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 考前 60 天日期選擇 (橫向捲動選單) ---
st.title("🏃‍♂️ 國中自然 60 天逆襲")
days = [f"Day {i}" for i in range(1, 61)]
selected_day = st.select_slider("滑動選擇衝刺進度：", options=days)

# 模擬資料庫 (未來可移至 Excel 或 Google Sheets)
content_map = {
    "Day 1": {"unit": "1-1 生命的起源與細胞", "audio": "day1.mp3", "img_prompt": "植物細胞與動物細胞結構對比圖"},
    "Day 2": {"unit": "1-2 養分與能量", "audio": "day2.mp3", "img_prompt": "人體消化系統構造圖"},
}

current_data = content_map.get(selected_day, {"unit": "內容準備中...", "audio": "", "img_prompt": ""})

# --- 3. 顯示單元主題與 AI 圖卡 ---
st.header(f"📍 當日進度：{current_data['unit']}")

# 這裡預留 AI 繪圖顯示區塊 (可以使用 Nano Banana 2 串接，或是預存圖)
st.info("💡 AI 複習圖卡：")
st.image("https://via.placeholder.com/600x400.png?text=AI+Cell+Structure+Image", 
         caption=f"AI 自動生成：{current_data['img_prompt']}")

# --- 4. Podcast 語音播放區 ---
st.subheader("🎧 課程 Podcast 監聽")
# 假設音檔放在 Google Cloud 或 GitHub 上的公開 URL
audio_url = f"https://your-cloud-storage.com/{current_data['audio']}" 
st.audio(audio_url, format="audio/mp3")

# --- 5. 打字機文字稿 (核心功能) ---
st.divider()
st.subheader("📝 逐字講義 (文字稿)")

def typewriter(text):
    container = st.empty()
    full_text = ""
    for char in text:
        full_text += char
        container.markdown(f'<div class="typing-text">{full_text}</div>', unsafe_allow_html=True)
        time.sleep(0.02)  # 調整打字速度

# 這裡放入我們產出的 3000 字腳本 (範例縮減版)
script_content = f"""
**大強老師：** 嘿！各位 Day {selected_day} 的戰友們，今天運動了嗎？...
**小美老師：** 沒錯，趕快放下手機，聽完這 8 分鐘再去操場跑兩圈！...
(這裡會是 2500-3000 字的完整腳本內容)
"""

if st.button("📖 展開/開始打字機閱讀"):
    typewriter(script_content)

# --- 6. 隨堂練習區 ---
st.divider()
with st.expander("📝 隨堂小測驗 (大強老師出題)"):
    q1 = st.radio("下列哪個構造是植物細胞有，但動物細胞沒有的？", ["細胞核", "粒線體", "細胞壁", "細胞膜"])
    if st.button("檢查答案"):
        if q1 == "細胞壁":
            st.success("正解！看來你今天多巴胺分泌很足夠喔！")
        else:
            st.error("哎呀，再去聽一次 Podcast 第 4 分鐘！")
