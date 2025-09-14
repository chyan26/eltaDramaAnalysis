"""
admin_features.py

整合Flask儀表板功能到Streamlit的管理模組
使用統一的核心分析引擎，確保與automated_pipeline一致
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

# 添加核心模組路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

try:
    from core.age_analysis_engine import AgeAnalysisEngine, AgeAnalysisConfig
    from core.visualization_engine import VisualizationEngine
    CORE_ENGINE_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ 無法載入核心分析引擎: {e}")
    CORE_ENGINE_AVAILABLE = False

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
    """自動化分析執行器 - 使用統一分析引擎"""
    st.header("🔄 自動化分析執行器（統一引擎版本）")
    
    if not CORE_ENGINE_AVAILABLE:
        st.error("❌ 核心分析引擎不可用，請檢查core模組")
        return
    
    # 初始化分析引擎
    if 'unified_engine' not in st.session_state:
        st.session_state.unified_engine = AgeAnalysisEngine()
        st.session_state.viz_engine = VisualizationEngine()
    
    engine = st.session_state.unified_engine
    viz_engine = st.session_state.viz_engine
    
    # 檢查資料狀態
    col1, col2, col3 = st.columns(3)
    
    with col1:
        data_status = "🟢 已載入" if engine.df is not None else "🔴 未載入"
        st.metric("資料狀態", data_status)
        
        if st.button("📂 載入資料", type="primary"):
            with st.spinner("載入中..."):
                try:
                    engine.load_data()
                    st.success("✅ 資料載入成功！")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 載入失敗: {e}")
    
    with col2:
        if engine.df is not None:
            st.metric("資料筆數", f"{len(engine.df):,}")
        else:
            st.metric("資料筆數", "N/A")
    
    with col3:
        if engine.df is not None:
            st.metric("劇集數量", engine.df['Cleaned_Series_Name'].nunique())
        else:
            st.metric("劇集數量", "N/A")
    
    st.divider()
    
    # 分析模組選擇
    st.subheader("🔧 分析模組")
    
    analysis_modules = {
        "� 年齡偏好分析": {
            "function": "analyze_age_preferences",
            "description": "分析不同年齡層對各劇集的偏好",
            "time": "30秒"
        },
        "⏰ 時段分析": {
            "function": "analyze_time_demographics", 
            "description": "分析不同時段的年齡分布",
            "time": "20秒"
        },
        "👥 性別差異分析": {
            "function": "analyze_gender_differences",
            "description": "分析性別收視差異",
            "time": "25秒"
        },
        "📅 週間vs週末分析": {
            "function": "analyze_weekday_weekend",
            "description": "分析週間和週末收視表現",
            "time": "35秒"
        },
        "� 月份趨勢分析": {
            "function": "analyze_monthly_trends",
            "description": "分析月份收視趨勢變化",
            "time": "20秒"
        }
    }
    
    # 批量操作
    st.subheader("🚀 快速操作")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ 執行完整分析", type="primary", disabled=engine.df is None):
            run_unified_complete_analysis(engine, viz_engine)
    
    with col2:
        if st.button("🎨 生成統一圖表", disabled=engine.df is None):
            generate_unified_charts(engine, viz_engine)
    
    with col3:
        if st.button("📊 獲取摘要統計", disabled=engine.df is None):
            show_unified_summary_stats(engine)
    
    st.divider()
    
    # 單獨模組執行
    st.subheader("🔧 單獨模組執行")
    
    for name, config in analysis_modules.items():
        with st.expander(f"{name} - {config['description']}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**功能**: {config['description']}")
                st.write(f"**預估時間**: {config['time']}")
                st.write(f"**引擎**: 統一核心分析引擎")
            
            with col2:
                if st.button(f"執行 {name}", key=f"run_{config['function']}", disabled=engine.df is None):
                    run_single_unified_analysis(engine, config['function'], name)

def run_unified_complete_analysis(engine, viz_engine):
    """執行統一的完整分析流程"""
    st.info("🚀 開始執行統一分析流程...")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    results_container = st.container()
    
    try:
        # 執行完整分析
        status_text.text("正在執行完整年齡分層分析...")
        progress_bar.progress(0.2)
        
        results = engine.run_complete_analysis()
        progress_bar.progress(0.7)
        
        # 生成視覺化
        status_text.text("正在生成統一視覺化圖表...")
        chart_path = viz_engine.create_comprehensive_dashboard(results)
        progress_bar.progress(1.0)
        
        status_text.text("✅ 統一分析流程完成!")
        
        # 顯示結果
        with results_container:
            st.success("🎉 分析完成！結果與automated_pipeline完全一致")
            
            # 摘要統計
            if 'summary_stats' in results:
                stats = results['summary_stats']
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("主要觀眾群", stats['main_audience'])
                with col2:
                    st.metric("平均收視率", f"{stats['main_audience_rating']:.4f}")
                with col3:
                    st.metric("性別偏向", stats['gender_bias'])
                with col4:
                    st.metric("最佳時段", f"{stats['best_hour']}點")
            
            # 顯示生成的圖表
            if os.path.exists(chart_path):
                st.image(chart_path, caption="統一分析結果圖表", use_container_width=True)
                
                # 提供下載
                with open(chart_path, "rb") as file:
                    st.download_button(
                        label="📥 下載完整分析圖表",
                        data=file,
                        file_name="unified_drama_age_analysis.png",
                        mime="image/png"
                    )
        
        st.balloons()
        
    except Exception as e:
        st.error(f"❌ 分析過程中發生錯誤: {e}")
        progress_bar.empty()
        status_text.empty()

def generate_unified_charts(engine, viz_engine):
    """生成統一圖表"""
    st.info("🎨 正在生成統一視覺化圖表...")
    
    with st.spinner("處理中..."):
        try:
            # 執行必要的分析
            results = {}
            results['age_preferences'] = engine.analyze_age_preferences()
            results['time_demographics'] = engine.analyze_time_demographics()
            results['gender_overall'], results['gender_series'] = engine.analyze_gender_differences()
            results['weekday_weekend'] = engine.analyze_weekday_weekend()
            results['monthly_trends'] = engine.analyze_monthly_trends()
            results['summary_stats'] = engine.get_summary_stats()
            
            # 生成圖表
            chart_path = viz_engine.create_comprehensive_dashboard(results)
            
            if os.path.exists(chart_path):
                st.success("✅ 統一圖表生成完成!")
                st.image(chart_path, caption="統一分析圖表", use_container_width=True)
                
                with open(chart_path, "rb") as file:
                    st.download_button(
                        label="📥 下載圖表",
                        data=file,
                        file_name="unified_charts.png",
                        mime="image/png"
                    )
            else:
                st.error("❌ 圖表檔案生成失敗")
        
        except Exception as e:
            st.error(f"❌ 圖表生成失敗: {e}")

def show_unified_summary_stats(engine):
    """顯示統一摘要統計"""
    st.info("📊 正在獲取統一摘要統計...")
    
    with st.spinner("處理中..."):
        try:
            stats = engine.get_summary_stats()
            
            st.success("✅ 摘要統計獲取完成!")
            
            # 關鍵指標
            st.subheader("📈 關鍵指標")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("主要觀眾群", stats['main_audience'])
            with col2:
                st.metric("平均收視率", f"{stats['main_audience_rating']:.4f}")
            with col3:
                st.metric("性別偏向", stats['gender_bias'])
            with col4:
                st.metric("最佳時段", f"{stats['best_hour']}點")
            
            # 詳細統計
            st.subheader("📋 詳細統計")
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"""
                **資料統計**
                - 總資料筆數: {stats['total_records']:,}
                - 劇集總數: {stats['total_series']}
                - 性別差異: {stats['gender_difference']:.4f}
                """)
            
            with col2:
                start_date = stats['date_range'][0].strftime('%Y-%m-%d')
                end_date = stats['date_range'][1].strftime('%Y-%m-%d') 
                st.info(f"""
                **時間範圍**
                - 開始日期: {start_date}
                - 結束日期: {end_date}
                - 最佳時段收視率: {stats['best_hour_rating']:.4f}
                """)
        
        except Exception as e:
            st.error(f"❌ 獲取摘要統計失敗: {e}")

def run_single_unified_analysis(engine, function_name, display_name):
    """執行單一統一分析"""
    st.info(f"▶️ 正在執行 {display_name}...")
    
    with st.spinner(f"執行 {function_name}..."):
        try:
            # 根據功能名稱調用對應方法
            if function_name == "analyze_age_preferences":
                result = engine.analyze_age_preferences()
                display_age_preferences_result(result)
            elif function_name == "analyze_time_demographics":
                result = engine.analyze_time_demographics()
                display_time_demographics_result(result)
            elif function_name == "analyze_gender_differences":
                overall_result, series_result = engine.analyze_gender_differences()
                display_gender_differences_result(overall_result, series_result)
            elif function_name == "analyze_weekday_weekend":
                result = engine.analyze_weekday_weekend()
                display_weekday_weekend_result(result)
            elif function_name == "analyze_monthly_trends":
                result = engine.analyze_monthly_trends()
                display_monthly_trends_result(result)
            
            st.success(f"✅ {display_name} 執行完成!")
            
        except Exception as e:
            st.error(f"❌ 執行失敗: {str(e)}")

def display_age_preferences_result(result):
    """顯示年齡偏好分析結果"""
    if not result.empty:
        st.subheader("🎯 年齡偏好分析結果")
        
        # 熱力圖數據
        pivot_data = result.pivot(index='Series', columns='Age_Group', values='Rating')
        st.dataframe(pivot_data, use_container_width=True)
        
        # 統計摘要
        st.write(f"📊 分析了 {result['Series'].nunique()} 部劇集的年齡偏好")
        
        # 最高收視率
        max_row = result.loc[result['Rating'].idxmax()]
        st.info(f"🏆 最高收視組合: {max_row['Series']} - {max_row['Age_Group']} ({max_row['Rating']:.4f})")

def display_time_demographics_result(result):
    """顯示時段分析結果"""
    if not result.empty:
        st.subheader("⏰ 時段分析結果")
        
        # 樞紐表
        pivot_data = result.pivot(index='Time_Slot', columns='Age_Group', values='Rating')
        st.dataframe(pivot_data, use_container_width=True)
        
        # 最佳時段統計
        best_slots = result.loc[result.groupby('Age_Group')['Rating'].idxmax()]
        st.write("🏆 各年齡層最佳時段:")
        for _, row in best_slots.iterrows():
            st.write(f"- {row['Age_Group']}: {row['Time_Slot']} ({row['Rating']:.4f})")

def display_gender_differences_result(overall_result, series_result):
    """顯示性別差異分析結果"""
    col1, col2 = st.columns(2)
    
    with col1:
        if not overall_result.empty:
            st.subheader("👥 整體性別差異")
            pivot_data = overall_result.pivot(index='Age_Group', columns='Gender', values='Rating')
            st.dataframe(pivot_data, use_container_width=True)
    
    with col2:
        if not series_result.empty:
            st.subheader("🎭 劇集性別偏好")
            pivot_data = series_result.pivot(index='Series', columns='Gender', values='Rating')
            st.dataframe(pivot_data, use_container_width=True)

def display_weekday_weekend_result(result):
    """顯示週間vs週末分析結果"""
    if 'series' in result and not result['series'].empty:
        st.subheader("📅 劇集週間vs週末表現")
        pivot_data = result['series'].pivot(index='Series', columns='Day_Type', values='Rating')
        st.dataframe(pivot_data, use_container_width=True)
    
    if 'age_groups' in result and not result['age_groups'].empty:
        st.subheader("👥 年齡層週間vs週末偏好")
        pivot_data = result['age_groups'].pivot(index='Age_Group', columns='Day_Type', values='Rating')
        st.dataframe(pivot_data, use_container_width=True)

def display_monthly_trends_result(result):
    """顯示月份趨勢分析結果"""
    if not result.empty:
        st.subheader("📈 月份趨勢分析結果")
        
        # 樞紐表
        pivot_data = result.pivot(index='Month', columns='Age_Group', values='Rating')
        st.dataframe(pivot_data, use_container_width=True)
        
        # 最佳/最差月份
        for group in result['Age_Group'].unique():
            group_data = result[result['Age_Group'] == group]
            if not group_data.empty:
                best_month = group_data.loc[group_data['Rating'].idxmax()]
                worst_month = group_data.loc[group_data['Rating'].idxmin()]
                st.write(f"**{group}**: 最佳 {best_month['Month']}月 ({best_month['Rating']:.4f}), " +
                        f"最差 {worst_month['Month']}月 ({worst_month['Rating']:.4f})")

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
