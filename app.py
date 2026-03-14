import streamlit as st
import pandas as pd
import requests
import base64

# --- 1. 頁面設定 ---
st.set_page_config(page_title="國中自然60天逆襲", layout="centered")

# --- 2. 路徑設定 (替換你的帳號) ---
USER = "flyer19820218"
REPO = "thelast60days"
GITHUB_RAW = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/"
# 使用 jsDelivr 服務來穩定顯示 PDF
PDF_URL = f"https://cdn.jsdelivr.net/gh/{USER}/{REPO}/notes.pdf"

@st.cache_data(ttl=60)
def load_data():
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1qcWBnMUgHVHO5XrN79NhVOWSnExzc8Mnc5wf4uUXbw4/export?format=csv"
    return pd.read_csv(SHEET_URL)

# --- 3. PDF 顯示功能 (修正版：使用 Google 服務跳板) ---
def display_pdf(url):
    # 利用 Google Drive PDF Viewer 繞過 GitHub 的嵌入限制
    google_view_url = f"https://docs.google.com/viewer?url={url}&embedded=true"
    pdf_display = f'<iframe src="{google_view_url}" width="100%" height="800" style="border: none;"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- 4. 主程式 ---
st.title("🎧 自然科學真理 PODCAST")
df = load_data()

if df is not None:
    # ... (中間選單代碼不變)
    
    # PDF 區
    st.divider()
    st.subheader("📝 彥君老師手繪講義")
    
    # 這裡要用 GitHub 的「真實原始連結」
    # 請確保 notes.pdf 是放在 Repo 的根目錄
    pdf_raw_url = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/notes.pdf"
    
    st.link_button("📂 全螢幕打開 PDF 講義", pdf_raw_url)
    
    # 呼叫修正後的顯示函數
    display_pdf(pdf_raw_url)
