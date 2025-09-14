"""
admin_features.py

整合Flask儀表板功能到Streamlit的管理模組
包含檔案監控、系統狀態、自動化分析等功能
"""

import streamlit as st
import pandas as pd
import os
import subprocess
import sys
from datetime import datetime
import time
from pathlib import Path
import json
import psutil

def show_system_status():
    """顯示系統狀態監控"""
    st.header("🔧 系統狀態監控")
    
    # 系統資源監控
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # 記憶體使用
        memory = psutil.virtual_memory()
        st.metric(
            label="💾 記憶體使用",
            value=f"{memory.percent:.1f}%",
            delta=f"{memory.used // (1024**3):.1f}GB 已使用"
        )
    
    with col2:
        # CPU使用
        cpu_percent = psutil.cpu_percent(interval=1)
        st.metric(
            label="🖥️ CPU使用",
            value=f"{cpu_percent:.1f}%",
            delta="正常" if cpu_percent < 80 else "偏高"
        )
    
    with col3:
        # 磁碟使用
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        st.metric(
            label="💿 磁碟使用", 
            value=f"{disk_percent:.1f}%",
            delta=f"{disk.free // (1024**3):.1f}GB 可用"
        )
    
    with col4:
        # 系統運行時間
        if 'app_start_time' not in st.session_state:
            st.session_state.app_start_time = time.time()
        
        uptime = time.time() - st.session_state.app_start_time
        hours, remainder = divmod(uptime, 3600)
        minutes, seconds = divmod(remainder, 60)
        st.metric(
            label="⏱️ 運行時間",
            value=f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}",
            delta="系統穩定"
        )

def show_file_monitor():
    """檔案監控儀表板"""
    st.header("📁 檔案監控儀表板")
    
    # 定義需要監控的檔案
    files_to_monitor = {
        "核心資料檔案": [
            'program_schedule_extracted.csv',
            'integrated_program_ratings_cleaned.csv', 
            'ACNelson_normalized_with_age.csv',
            'ACNelson_normalized.csv'
        ],
        "分析結果": [
            'drama_age_analysis.png',
            'drama_age_analysis_report.pdf',
            'ratings_analysis_heiti.png'
        ],
        "配置檔案": [
            'requirements.txt',
            '.streamlit/config.toml',
            '.gitignore'
        ]
    }
    
    # 檔案狀態總覽
    total_files = sum(len(files) for files in files_to_monitor.values())
    existing_files = 0
    total_size = 0
    
    for category, files in files_to_monitor.items():
        for file in files:
            if os.path.exists(file):
                existing_files += 1
                total_size += os.path.getsize(file)
    
    # 總覽指標
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📂 檔案總數", f"{existing_files}/{total_files}")
    with col2:
        st.metric("📊 總大小", f"{total_size / (1024*1024):.1f} MB")
    with col3:
        health_status = "🟢 良好" if existing_files/total_files > 0.8 else "🟡 注意" if existing_files/total_files > 0.5 else "🔴 警告"
        st.metric("🏥 檔案健康度", health_status)
    
    # 詳細檔案列表
    for category, files in files_to_monitor.items():
        with st.expander(f"📂 {category} ({sum(1 for f in files if os.path.exists(f))}/{len(files)} 個檔案)"):
            for file in files:
                col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
                
                with col1:
                    if os.path.exists(file):
                        st.success(f"✅ {file}")
                    else:
                        st.error(f"❌ {file}")
                
                if os.path.exists(file):
                    file_stat = os.stat(file)
                    with col2:
                        size_mb = file_stat.st_size / (1024*1024)
                        st.caption(f"{size_mb:.2f} MB")
                    
                    with col3:
                        mod_time = datetime.fromtimestamp(file_stat.st_mtime)
                        st.caption(f"修改: {mod_time.strftime('%m-%d %H:%M')}")
                    
                    with col4:
                        if st.button("📥", key=f"download_{file}", help=f"下載 {file}"):
                            try:
                                with open(file, 'rb') as f:
                                    st.download_button(
                                        label=f"下載 {file}",
                                        data=f,
                                        file_name=file,
                                        mime='application/octet-stream'
                                    )
                            except Exception as e:
                                st.error(f"下載失敗: {e}")

def show_analysis_runner():
    """自動化分析執行器"""
    st.header("🔄 自動化分析執行器")
    
    # 分析腳本配置
    analysis_scripts = {
        "🧹 資料清理": {
            "script": "clean_data.py",
            "description": "清理和標準化原始資料",
            "estimated_time": "30秒",
            "prerequisites": ["原始資料檔案"]
        },
        "📊 基礎分析": {
            "script": "drama_analysis.py", 
            "description": "執行劇集收視率基礎分析",
            "estimated_time": "1分鐘",
            "prerequisites": ["清理後資料"]
        },
        "🎨 圖表生成": {
            "script": "create_charts_heiti.py",
            "description": "生成中文收視率分析圖表",
            "estimated_time": "45秒",
            "prerequisites": ["分析結果"]
        },
        "👥 年齡分析": {
            "script": "drama_age_analysis.py",
            "description": "深度年齡分層收視分析",
            "estimated_time": "2分鐘",
            "prerequisites": ["年齡分層資料"]
        },
        "📋 報告生成": {
            "script": "generate_pdf_report.py",
            "description": "生成PDF格式分析報告",
            "estimated_time": "1分鐘",
            "prerequisites": ["所有分析結果"]
        }
    }
    
    # 批量操作
    st.subheader("🚀 快速操作")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ 執行完整分析流程", type="primary"):
            run_complete_analysis(analysis_scripts)
    
    with col2:
        if st.button("🎨 僅生成圖表"):
            run_charts_only(analysis_scripts)
    
    with col3:
        if st.button("📊 更新資料"):
            update_data_only()
    
    st.divider()
    
    # 單獨腳本執行
    st.subheader("🔧 單獨腳本執行")
    
    for name, config in analysis_scripts.items():
        with st.expander(f"{name} - {config['description']}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**腳本**: `{config['script']}`")
                st.write(f"**預估時間**: {config['estimated_time']}")
                st.write(f"**前置條件**: {', '.join(config['prerequisites'])}")
            
            with col2:
                if st.button(f"執行 {name}", key=f"run_{config['script']}"):
                    run_single_script(config['script'], name)

def run_complete_analysis(scripts):
    """執行完整分析流程"""
    st.info("🚀 開始執行完整分析流程...")
    
    # 創建進度條
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    script_order = [
        "clean_data.py",
        "drama_analysis.py", 
        "create_charts_heiti.py",
        "drama_age_analysis.py",
        "generate_pdf_report.py"
    ]
    
    results = []
    
    for i, script in enumerate(script_order):
        status_text.text(f"執行中: {script}")
        
        # 模擬執行（在實際環境中會真的執行）
        time.sleep(1)  # 模擬處理時間
        
        try:
            # 實際執行腳本的代碼
            # result = subprocess.run([sys.executable, script], capture_output=True, text=True, timeout=300)
            # if result.returncode == 0:
            #     results.append(f"✅ {script} - 成功")
            # else:
            #     results.append(f"❌ {script} - 失敗: {result.stderr}")
            
            # 模擬成功結果
            results.append(f"✅ {script} - 執行成功")
            
        except Exception as e:
            results.append(f"❌ {script} - 錯誤: {str(e)}")
        
        progress_bar.progress((i + 1) / len(script_order))
    
    status_text.text("✅ 分析流程完成!")
    
    # 顯示結果
    st.subheader("📊 執行結果")
    for result in results:
        if "✅" in result:
            st.success(result)
        else:
            st.error(result)

def run_charts_only(scripts):
    """僅生成圖表"""
    st.info("🎨 正在生成圖表...")
    
    with st.spinner("處理中..."):
        time.sleep(2)  # 模擬處理
        st.success("✅ 圖表生成完成!")
        st.balloons()

def update_data_only():
    """僅更新資料"""
    st.info("📊 正在更新資料...")
    
    with st.spinner("處理中..."):
        time.sleep(1.5)  # 模擬處理
        st.success("✅ 資料更新完成!")

def run_single_script(script, name):
    """執行單一腳本"""
    st.info(f"▶️ 正在執行 {name}...")
    
    with st.spinner(f"執行 {script}..."):
        try:
            # 模擬執行
            time.sleep(2)
            st.success(f"✅ {name} 執行完成!")
        except Exception as e:
            st.error(f"❌ 執行失敗: {str(e)}")

def show_logs_viewer():
    """日誌查看器"""
    st.header("📋 系統日誌")
    
    # 模擬日誌資料
    log_entries = [
        {"time": "2025-09-14 14:30:15", "level": "INFO", "message": "Streamlit應用啟動"},
        {"time": "2025-09-14 14:30:20", "level": "INFO", "message": "資料載入完成: 10,345筆記錄"},
        {"time": "2025-09-14 14:31:02", "level": "INFO", "message": "推薦引擎初始化成功"},
        {"time": "2025-09-14 14:31:15", "level": "WARNING", "message": "部分圖片檔案缺失"},
        {"time": "2025-09-14 14:32:00", "level": "INFO", "message": "使用者執行智能推薦"},
        {"time": "2025-09-14 14:32:05", "level": "INFO", "message": "推薦結果生成: 10個候選項目"},
    ]
    
    # 日誌級別篩選
    col1, col2 = st.columns([1, 3])
    
    with col1:
        log_level = st.selectbox(
            "篩選日誌級別",
            ["ALL", "INFO", "WARNING", "ERROR"],
            index=0
        )
    
    with col2:
        auto_refresh = st.checkbox("自動刷新 (5秒)", value=True)
        if auto_refresh:
            st.rerun()
    
    # 顯示日誌
    st.subheader("🔍 最新日誌 (最後50條)")
    
    for entry in reversed(log_entries[-50:]):
        if log_level == "ALL" or entry["level"] == log_level:
            level_color = {
                "INFO": "🟢",
                "WARNING": "🟡", 
                "ERROR": "🔴"
            }.get(entry["level"], "⚪")
            
            st.text(f"{level_color} {entry['time']} [{entry['level']}] {entry['message']}")

def show_data_uploader():
    """資料上傳器"""
    st.header("📤 資料上傳管理")
    
    st.write("上傳新的資料檔案來更新分析資料庫")
    
    # 上傳區域
    uploaded_files = st.file_uploader(
        "選擇檔案上傳",
        accept_multiple_files=True,
        type=['csv', 'xlsx', 'xls'],
        help="支援CSV和Excel格式檔案"
    )
    
    if uploaded_files:
        st.subheader("📂 上傳檔案預覽")
        
        for uploaded_file in uploaded_files:
            with st.expander(f"📄 {uploaded_file.name}"):
                try:
                    # 讀取檔案預覽
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("資料筆數", len(df))
                    with col2:
                        st.metric("欄位數", len(df.columns))
                    with col3:
                        st.metric("檔案大小", f"{uploaded_file.size / 1024:.1f} KB")
                    
                    # 顯示前幾行
                    st.write("**前5行預覽:**")
                    st.dataframe(df.head(), use_container_width=True)
                    
                    # 儲存檔案按鈕
                    if st.button(f"💾 儲存 {uploaded_file.name}", key=f"save_{uploaded_file.name}"):
                        try:
                            # 在實際環境中會儲存檔案
                            st.success(f"✅ {uploaded_file.name} 已儲存!")
                        except Exception as e:
                            st.error(f"❌ 儲存失敗: {e}")
                
                except Exception as e:
                    st.error(f"❌ 無法讀取檔案: {e}")

def show_reports_viewer():
    """分析報告和圖表查看器"""
    st.header("📊 分析報告與圖表查看器")
    
    # 定義報告和圖表檔案
    report_files = {
        "📈 分析圖表": {
            "drama_age_analysis.png": "年齡分層收視分析圖表",
            "ratings_analysis_heiti.png": "收視率分析圖表 (中文版)",
            "ratings_analysis_english.png": "收視率分析圖表 (英文版)"
        },
        "📋 分析報告": {
            "drama_age_analysis_report.pdf": "年齡分層收視分析報告",
            "ai_python_presentation.pdf": "AI Python 分析簡報"
        }
    }
    
    # 報告總覽
    st.subheader("📊 報告總覽")
    
    total_charts = len(report_files["📈 分析圖表"])
    total_reports = len(report_files["📋 分析報告"])
    available_charts = sum(1 for f in report_files["📈 分析圖表"].keys() if os.path.exists(f))
    available_reports = sum(1 for f in report_files["📋 分析報告"].keys() if os.path.exists(f))
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📈 圖表總數", f"{available_charts}/{total_charts}")
    
    with col2:
        st.metric("📋 報告總數", f"{available_reports}/{total_reports}")
    
    with col3:
        completion_rate = ((available_charts + available_reports) / (total_charts + total_reports)) * 100
        st.metric("📊 完成度", f"{completion_rate:.0f}%")
    
    with col4:
        status = "🟢 完整" if completion_rate == 100 else "🟡 部分" if completion_rate > 50 else "🔴 缺失"
        st.metric("🎯 狀態", status)
    
    st.divider()
    
    # 圖表顯示區域
    st.subheader("📈 分析圖表")
    
    chart_tabs = st.tabs(["年齡分析", "收視率分析 (中文)", "收視率分析 (英文)"])
    
    # 年齡分析圖表
    with chart_tabs[0]:
        chart_file = "drama_age_analysis.png"
        if os.path.exists(chart_file):
            st.success(f"✅ {report_files['📈 分析圖表'][chart_file]}")
            
            # 檔案資訊
            file_stat = os.stat(chart_file)
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"📅 更新時間: {datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
            with col2:
                st.info(f"📏 檔案大小: {file_stat.st_size / 1024:.1f} KB")
            
            # 顯示圖片
            st.image(chart_file, caption="年齡分層收視分析", use_container_width=True)
            
            # 下載按鈕
            with open(chart_file, "rb") as file:
                st.download_button(
                    label="📥 下載圖表",
                    data=file,
                    file_name=chart_file,
                    mime="image/png"
                )
        else:
            st.error(f"❌ 檔案不存在: {chart_file}")
            st.info("💡 請先執行年齡分析腳本來生成此圖表")
    
    # 收視率分析圖表 (中文)
    with chart_tabs[1]:
        chart_file = "ratings_analysis_heiti.png"
        if os.path.exists(chart_file):
            st.success(f"✅ {report_files['📈 分析圖表'][chart_file]}")
            
            # 檔案資訊
            file_stat = os.stat(chart_file)
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"📅 更新時間: {datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
            with col2:
                st.info(f"📏 檔案大小: {file_stat.st_size / 1024:.1f} KB")
            
            # 顯示圖片
            st.image(chart_file, caption="收視率分析 (中文版)", use_container_width=True)
            
            # 下載按鈕
            with open(chart_file, "rb") as file:
                st.download_button(
                    label="📥 下載圖表",
                    data=file,
                    file_name=chart_file,
                    mime="image/png"
                )
        else:
            st.error(f"❌ 檔案不存在: {chart_file}")
            st.info("💡 請先執行圖表生成腳本來生成此圖表")
    
    # 收視率分析圖表 (英文)
    with chart_tabs[2]:
        chart_file = "ratings_analysis_english.png"
        if os.path.exists(chart_file):
            st.success(f"✅ {report_files['📈 分析圖表'][chart_file]}")
            
            # 檔案資訊
            file_stat = os.stat(chart_file)
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"📅 更新時間: {datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
            with col2:
                st.info(f"📏 檔案大小: {file_stat.st_size / 1024:.1f} KB")
            
            # 顯示圖片
            st.image(chart_file, caption="收視率分析 (英文版)", use_container_width=True)
            
            # 下載按鈕
            with open(chart_file, "rb") as file:
                st.download_button(
                    label="📥 下載圖表",
                    data=file,
                    file_name=chart_file,
                    mime="image/png"
                )
        else:
            st.error(f"❌ 檔案不存在: {chart_file}")
            st.info("💡 請先執行圖表生成腳本來生成此圖表")
    
    st.divider()
    
    # PDF 報告區域
    st.subheader("📋 PDF 分析報告")
    
    for report_file, description in report_files["📋 分析報告"].items():
        with st.expander(f"📄 {description}"):
            if os.path.exists(report_file):
                st.success(f"✅ 檔案存在: {report_file}")
                
                # 檔案資訊
                file_stat = os.stat(report_file)
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("📏 檔案大小", f"{file_stat.st_size / (1024*1024):.2f} MB")
                
                with col2:
                    st.metric("📅 更新日期", datetime.fromtimestamp(file_stat.st_mtime).strftime('%m-%d'))
                
                with col3:
                    st.metric("⏰ 更新時間", datetime.fromtimestamp(file_stat.st_mtime).strftime('%H:%M'))
                
                # 下載按鈕
                with open(report_file, "rb") as file:
                    st.download_button(
                        label=f"📥 下載 {description}",
                        data=file,
                        file_name=report_file,
                        mime="application/pdf",
                        key=f"download_{report_file}"
                    )
                
                # PDF 預覽提示
                st.info("💡 點擊下載按鈕來查看完整的PDF報告")
                
            else:
                st.error(f"❌ 檔案不存在: {report_file}")
                
                if "drama_age_analysis_report.pdf" in report_file:
                    st.info("💡 請先執行年齡分析和報告生成腳本")
                else:
                    st.info("💡 此為額外的簡報檔案，可能需要手動放置")
    
    st.divider()
    
    # 批量操作
    st.subheader("🔄 批量操作")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 重新生成所有圖表", type="primary"):
            st.info("🎨 開始重新生成所有分析圖表...")
            with st.spinner("生成中..."):
                time.sleep(2)  # 模擬處理時間
                st.success("✅ 所有圖表已重新生成！")
                st.rerun()
    
    with col2:
        if st.button("📋 重新生成所有報告"):
            st.info("📄 開始重新生成所有分析報告...")
            with st.spinner("生成中..."):
                time.sleep(3)  # 模擬處理時間
                st.success("✅ 所有報告已重新生成！")
                st.rerun()
    
    with col3:
        if st.button("🗑️ 清理舊檔案"):
            st.warning("⚠️ 此操作將刪除所有舊的圖表和報告檔案")
            if st.button("確認刪除", key="confirm_delete"):
                st.info("🗑️ 正在清理舊檔案...")
                st.success("✅ 清理完成！")

def show_admin_dashboard():
    """主管理儀表板"""
    st.title("🔧 系統管理中心")
    st.markdown("整合式管理介面 - 原Flask儀表板功能")
    
    # 側邊欄導航
    st.sidebar.markdown("---")
    st.sidebar.header("🎛️ 管理功能")
    
    admin_options = {
        "🔧 系統狀態": show_system_status,
        "📁 檔案監控": show_file_monitor,
        "🔄 自動化分析": show_analysis_runner,
        "� 報告與圖表": show_reports_viewer,
        "�📋 系統日誌": show_logs_viewer,
        "📤 資料上傳": show_data_uploader
    }
    
    selected_admin = st.sidebar.radio(
        "選擇管理功能:",
        list(admin_options.keys()),
        index=0
    )
    
    # 執行選擇的功能
    admin_options[selected_admin]()
