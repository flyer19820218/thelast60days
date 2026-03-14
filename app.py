# --- 文字區：Spotify 劇本字幕模式 ---
    st.divider()
    st.subheader("💬 衝刺劇本 (對話字幕)")
    
    script_path = str(row['Script_Path']).strip()
    if script_path.startswith('/'): script_path = script_path[1:]
    script_url = f"{GITHUB_RAW}{script_path}"
    
    try:
        res = requests.get(script_url)
        res.encoding = 'utf-8'
        lines = res.text.split('\n')
        
        # 建立一個有高度限制、可手動滾動的字幕視窗
        chat_html = '<div style="height: 400px; overflow-y: auto; padding: 15px; background-color: #f4f6f9; border-radius: 10px; border: 1px solid #ddd;">'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 💡 關鍵修正：HTML 標籤全部寫在同一行，絕對不准縮排！
            if "彥君老師：" in line:
                content = line.replace("彥君老師：", "").strip()
                chat_html += f'<div style="margin-bottom: 15px; text-align: left;"><span style="background-color: #e3f2fd; padding: 10px 15px; border-radius: 15px; display: inline-block; max-width: 85%; color: #000; box-shadow: 1px 1px 3px rgba(0,0,0,0.1);"><b>👨‍🏫 彥君老師</b><br>{content}</span></div>'
            elif "曉臻助教：" in line:
                content = line.replace("曉臻助教：", "").strip()
                chat_html += f'<div style="margin-bottom: 15px; text-align: right;"><span style="background-color: #ffe0b2; padding: 10px 15px; border-radius: 15px; display: inline-block; max-width: 85%; text-align: left; color: #000; box-shadow: 1px 1px 3px rgba(0,0,0,0.1);"><b>👩‍🔬 曉臻助教</b><br>{content}</span></div>'
            else:
                # 其他旁白或標題
                chat_html += f'<div style="text-align: center; color: #888; font-size: 0.9em; margin: 10px 0;">{line}</div>'
                
        chat_html += '</div>'
        
        # 顯示對話框
        st.markdown(chat_html, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"劇本載入失敗。請檢查 {script_url} 是否存在。")
