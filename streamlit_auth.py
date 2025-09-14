import streamlit as st

# 密碼保護設置
def check_password():
    """簡單的密碼保護"""
    
    def password_entered():
        """檢查密碼是否正確"""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # 清除密碼
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # 首次訪問，顯示密碼輸入
        st.text_input(
            "🔐 請輸入系統密碼", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.info("請聯繫系統管理員獲取訪問密碼")
        return False
    elif not st.session_state["password_correct"]:
        # 密碼錯誤
        st.text_input(
            "🔐 請輸入系統密碼", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.error("❌ 密碼錯誤，請重試")
        return False
    else:
        # 密碼正確
        return True

# 環境配置檢查
def check_environment():
    """檢查生產環境配置"""
    required_files = [
        "program_schedule_extracted.csv",
        "integrated_program_ratings_cleaned.csv"
    ]
    
    missing_files = []
    for file in required_files:
        try:
            import os
            if not os.path.exists(file):
                missing_files.append(file)
        except:
            missing_files.append(file)
    
    if missing_files:
        st.error(f"❌ 缺少必要檔案：{', '.join(missing_files)}")
        st.info("請確保所有資料檔案都已上傳到伺服器")
        return False
    
    return True

# 效能監控
def add_performance_metrics():
    """添加效能監控指標"""
    import time
    import psutil
    
    # 記錄頁面載入時間
    if 'start_time' not in st.session_state:
        st.session_state.start_time = time.time()
    
    # 在側邊欄顯示系統資訊
    with st.sidebar:
        st.subheader("🔧 系統資訊")
        
        # 運行時間
        runtime = time.time() - st.session_state.start_time
        st.metric("運行時間", f"{runtime:.1f}秒")
        
        # 記憶體使用
        memory = psutil.virtual_memory()
        st.metric("記憶體使用", f"{memory.percent:.1f}%")
        
        # CPU使用
        cpu = psutil.cpu_percent(interval=1)
        st.metric("CPU使用", f"{cpu:.1f}%")
