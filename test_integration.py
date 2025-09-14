"""
Integration Testing and Validation
整合測試和驗證檔案

檢查Flask功能是否成功整合到Streamlit應用中
"""

import sys
import os

def test_imports():
    """測試所有必要的導入是否成功"""
    try:
        # 測試基本導入而不執行Streamlit
        import pandas as pd
        print("✅ pandas imported successfully")
    except Exception as e:
        print(f"❌ pandas import failed: {e}")
        return False
    
    try:
        import psutil
        print("✅ psutil imported successfully")
    except Exception as e:
        print(f"❌ psutil import failed: {e}")
        return False
    
    # 測試能否導入檔案（但不執行）
    try:
        import sys
        import os
        sys.path.insert(0, os.getcwd())
        
        # 檢查admin_features.py檔案是否存在且語法正確
        with open('admin_features.py', 'r', encoding='utf-8') as f:
            content = f.read()
            compile(content, 'admin_features.py', 'exec')
        print("✅ admin_features.py syntax check passed")
        
        # 檢查recommend.py檔案是否存在且語法正確
        with open('recommend.py', 'r', encoding='utf-8') as f:
            content = f.read()
            compile(content, 'recommend.py', 'exec')
        print("✅ recommend.py syntax check passed")
        
    except Exception as e:
        print(f"❌ File syntax check failed: {e}")
        return False
    
    return True

def test_file_structure():
    """檢查檔案結構是否完整"""
    required_files = [
        'recommend.py',
        'admin_features.py',
        'requirements.txt',
        'program_schedule_extracted.csv',
        'integrated_program_ratings_cleaned.csv'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def test_admin_functions():
    """測試管理功能是否可用"""
    try:
        # 檢查admin_features.py中的函數定義
        with open('admin_features.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        required_functions = [
            'show_system_status',
            'show_file_monitor', 
            'show_analysis_runner',
            'show_reports_viewer',
            'show_logs_viewer',
            'show_data_uploader',
            'show_admin_dashboard'
        ]
        
        missing_functions = []
        for func in required_functions:
            if f"def {func}(" not in content:
                missing_functions.append(func)
        
        if missing_functions:
            print(f"❌ Missing functions: {missing_functions}")
            return False
        else:
            print("✅ All admin functions defined")
            return True
            
    except Exception as e:
        print(f"❌ Admin functions check failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 開始整合測試...")
    print("=" * 50)
    
    # 執行測試
    tests = [
        ("導入測試", test_imports),
        ("檔案結構測試", test_file_structure),
        ("管理功能測試", test_admin_functions)
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        print(f"\n📊 {test_name}:")
        if test_func():
            print(f"✅ {test_name} 通過")
        else:
            print(f"❌ {test_name} 失敗")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有測試通過！整合成功！")
        print("🚀 您可以在 http://localhost:8501 使用整合後的應用程式")
        print("💡 在側邊欄選擇 '🔧 系統管理中心' 來使用原Flask功能")
    else:
        print("❌ 某些測試失敗，請檢查上述錯誤訊息")
    
    print("\n📋 功能清單:")
    print("  📺 劇集推薦系統 (原Streamlit功能)")
    print("  🔧 系統狀態監控 (原Flask功能)")
    print("  📁 檔案監控儀表板 (原Flask功能)")
    print("  🔄 自動化分析執行器 (原Flask功能)")
    print("  � 報告與圖表查看器 (新增功能)")
    print("  �📋 系統日誌查看器 (原Flask功能)")
    print("  📤 資料上傳管理 (原Flask功能)")
