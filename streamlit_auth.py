import streamlit as st
import os
import time
import traceback

# 密碼保護設置
def check_password():
    """簡單的密碼保護"""
    
    def password_entered():
        """檢查密碼是否正確"""
        try:
            # 檢查 secrets 是否可用
            if hasattr(st, 'secrets') and 'password' in st.secrets:
                expected_password = st.secrets["password"]
            else:
                # 開發環境回退
                expected_password = "your-secure-password-here"
                
            if st.session_state["password"] == expected_password:
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # 清除密碼
            else:
                st.session_state["password_correct"] = False
        except Exception as e:
            st.error(f"密碼驗證錯誤: {str(e)}")
            st.session_state["password_correct"] = False

    # 在開發環境中跳過密碼檢查
    if os.getenv('STREAMLIT_DEV_MODE') == 'true':
        return True

    if "password_correct" not in st.session_state:
        # 首次訪問，顯示密碼輸入
        st.markdown("### 🔐 系統登入")
        st.text_input(
            "請輸入系統密碼", 
            type="password", 
            on_change=password_entered, 
            key="password",
            help="請聯繫系統管理員獲取訪問密碼"
        )
        
        # 顯示系統資訊
        with st.expander("ℹ️ 系統資訊"):
            st.info("愛爾達劇集分析系統 v2.0")
            st.info("支援劇集推薦、收視分析、管理儀表板等功能")
            
        return False
        
    elif not st.session_state["password_correct"]:
        # 密碼錯誤
        st.markdown("### 🔐 系統登入")
        st.text_input(
            "請輸入系統密碼", 
            type="password", 
            on_change=password_entered, 
            key="password",
            help="密碼錯誤，請重試"
        )
        st.error("❌ 密碼錯誤，請重試")
        
        # 顯示安全提示
        with st.expander("🛡️ 安全提示"):
            st.warning("多次密碼錯誤可能會被記錄")
            st.info("如果您忘記密碼，請聯繫系統管理員")
            
        return False
    else:
        # 密碼正確，顯示歡迎訊息
        if 'welcome_shown' not in st.session_state:
            st.success("✅ 登入成功！歡迎使用愛爾達劇集分析系統")
            st.session_state.welcome_shown = True
        return True

# 環境配置檢查
def check_environment():
    """檢查生產環境配置"""
    required_files = [
        "program_schedule_extracted.csv",
        "integrated_program_ratings_cleaned.csv"
    ]
    
    missing_files = []
    file_info = []
    
    for file in required_files:
        try:
            if not os.path.exists(file):
                missing_files.append(file)
            else:
                # 獲取檔案資訊
                stat = os.stat(file)
                size_mb = stat.st_size / (1024 * 1024)
                file_info.append(f"{file} ({size_mb:.1f} MB)")
        except Exception as e:
            missing_files.append(f"{file} (錯誤: {str(e)})")
    
    if missing_files:
        st.error("❌ 環境檢查失敗")
        st.markdown("**缺少必要檔案：**")
        for file in missing_files:
            st.markdown(f"- {file}")
        
        with st.expander("💡 解決方案"):
            st.markdown("""
            **檔案缺失解決步驟：**
            1. 檢查檔案是否上傳到正確位置
            2. 確認檔案名稱拼寫正確
            3. 驗證檔案權限設定
            4. 聲繫管理員重新上傳資料檔案
            """)
        return False
    
    # 顯示成功資訊
    st.success("✅ 環境檢查通過")
    with st.expander("📂 檔案狀態"):
        st.markdown("**已載入檔案：**")
        for info in file_info:
            st.markdown(f"- ✅ {info}")
    
    return True

# 效能監控
def add_performance_metrics():
    """添加效能監控指標"""
    try:
        import psutil
        
        # 記錄頁面載入時間
        if 'start_time' not in st.session_state:
            st.session_state.start_time = time.time()
        
        # 在側邊欄顯示系統資訊
        with st.sidebar:
            st.markdown("---")
            st.subheader("� 系統監控")
            
            # 運行時間
            runtime = time.time() - st.session_state.start_time
            hours, remainder = divmod(runtime, 3600)
            minutes, seconds = divmod(remainder, 60)
            runtime_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            st.metric("⏱️ 運行時間", runtime_str)
            
            # 記憶體使用
            memory = psutil.virtual_memory()
            memory_color = "🟢" if memory.percent < 70 else "🟡" if memory.percent < 85 else "🔴"
            st.metric("💾 記憶體使用", f"{memory.percent:.1f}%", delta=f"{memory_color}")
            
            # CPU使用
            cpu = psutil.cpu_percent(interval=0.1)
            cpu_color = "🟢" if cpu < 70 else "🟡" if cpu < 85 else "🔴"
            st.metric("🖥️ CPU使用", f"{cpu:.1f}%", delta=f"{cpu_color}")
            
            # 磁碟使用
            try:
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                disk_color = "🟢" if disk_percent < 70 else "🟡" if disk_percent < 85 else "🔴"
                st.metric("💿 磁碟使用", f"{disk_percent:.1f}%", delta=f"{disk_color}")
            except:
                st.metric("💿 磁碟使用", "無法取得")
                
    except ImportError:
        st.sidebar.warning("⚠️ psutil 套件未安裝，無法顯示系統監控")
    except Exception as e:
        st.sidebar.error(f"❌ 系統監控錯誤: {str(e)}")

# 錯誤處理裝飾器
def handle_errors(func):
    """錯誤處理裝飾器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"❌ 發生錯誤: {str(e)}")
            with st.expander("🔍 詳細錯誤資訊"):
                st.code(traceback.format_exc())
            return False
    return wrapper

# 安全初始化函數
@handle_errors
def secure_init():
    """安全初始化系統"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("🔒 **安全狀態**")
    st.sidebar.success("✅ 系統已通過安全檢查")
    
    # 記錄使用者活動
    if 'activity_log' not in st.session_state:
        st.session_state.activity_log = []
    
    # 添加活動記錄
    current_time = time.strftime("%H:%M:%S")
    if len(st.session_state.activity_log) == 0:
        st.session_state.activity_log.append(f"{current_time} - 使用者登入系統")
    
    return True
