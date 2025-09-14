"""
streamlit_unified_analysis.py

統一分析引擎的Streamlit介面
展示與automated_pipeline一致的分析結果
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
from datetime import datetime
import time

# 添加核心模組路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

try:
    from core.age_analysis_engine import AgeAnalysisEngine, AgeAnalysisConfig
    from core.visualization_engine import VisualizationEngine
    UNIFIED_ENGINE_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ 無法載入統一分析引擎: {e}")
    UNIFIED_ENGINE_AVAILABLE = False

def main():
    """主要應用程式"""
    st.set_page_config(
        page_title="愛爾達統一分析系統",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 標題和介紹
    st.title("🎬 愛爾達統一年齡分層分析系統")
    st.markdown("### 🔧 與automated_pipeline使用相同的核心分析引擎")
    
    if not UNIFIED_ENGINE_AVAILABLE:
        st.error("❌ 統一分析引擎不可用，請檢查core模組是否正確安裝")
        return
    
    # 初始化引擎
    initialize_engines()
    
    # 側邊欄
    create_sidebar()
    
    # 主要內容
    create_main_content()

def initialize_engines():
    """初始化分析引擎"""
    if 'unified_engine' not in st.session_state:
        with st.spinner("初始化統一分析引擎..."):
            st.session_state.unified_engine = AgeAnalysisEngine()
            st.session_state.viz_engine = VisualizationEngine()
            st.session_state.data_loaded = False
            st.session_state.analysis_results = None
        st.success("✅ 統一分析引擎初始化完成")

def create_sidebar():
    """創建側邊欄"""
    st.sidebar.header("🔧 系統控制")
    
    # 資料載入狀態
    engine = st.session_state.unified_engine
    data_status = "🟢 已載入" if st.session_state.data_loaded else "🔴 未載入"
    st.sidebar.metric("資料狀態", data_status)
    
    if st.session_state.data_loaded and engine.df is not None:
        st.sidebar.metric("資料筆數", f"{len(engine.df):,}")
        st.sidebar.metric("劇集數量", engine.df['Cleaned_Series_Name'].nunique())
        date_range = engine.df['Date'].agg(['min', 'max'])
        st.sidebar.write(f"📅 {date_range['min'].date()} 至 {date_range['max'].date()}")
    
    st.sidebar.divider()
    
    # 資料載入按鈕
    if st.sidebar.button("📂 載入資料", type="primary"):
        load_data()
    
    # 分析參數設定
    st.sidebar.subheader("⚙️ 分析參數")
    min_episodes = st.sidebar.slider("最少集數", 10, 100, 50)
    top_n_series = st.sidebar.slider("分析劇集數", 5, 20, 10)
    
    # 儲存參數到session state
    st.session_state.min_episodes = min_episodes
    st.session_state.top_n_series = top_n_series
    
    st.sidebar.divider()
    
    # 快速操作
    st.sidebar.subheader("🚀 快速操作")
    
    if st.sidebar.button("▶️ 執行完整分析", disabled=not st.session_state.data_loaded):
        run_complete_analysis()
    
    if st.sidebar.button("🎨 生成視覺化", disabled=not st.session_state.data_loaded):
        generate_visualizations()
    
    if st.sidebar.button("📊 獲取摘要", disabled=not st.session_state.data_loaded):
        get_summary_stats()

def load_data():
    """載入資料"""
    try:
        with st.spinner("載入資料中..."):
            engine = st.session_state.unified_engine
            engine.load_data()
            st.session_state.data_loaded = True
        
        st.success(f"✅ 資料載入成功！共 {len(engine.df):,} 筆記錄")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ 資料載入失敗: {e}")

def run_complete_analysis():
    """執行完整分析"""
    try:
        with st.spinner("執行統一完整分析..."):
            engine = st.session_state.unified_engine
            
            # 執行完整分析
            results = engine.run_complete_analysis(
                min_episodes=st.session_state.min_episodes,
                top_n=st.session_state.top_n_series
            )
            
            st.session_state.analysis_results = results
        
        st.success("🎉 完整分析執行完成！與automated_pipeline結果一致")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ 分析執行失敗: {e}")

def generate_visualizations():
    """生成視覺化圖表"""
    try:
        if st.session_state.analysis_results is None:
            st.warning("請先執行完整分析")
            return
        
        with st.spinner("生成統一視覺化圖表..."):
            viz_engine = st.session_state.viz_engine
            chart_path = viz_engine.create_comprehensive_dashboard(
                st.session_state.analysis_results,
                'streamlit_unified_analysis.png'
            )
        
        st.success("✅ 統一視覺化圖表生成完成")
        
        # 顯示圖表
        if os.path.exists(chart_path):
            st.image(chart_path, caption="統一分析結果", use_container_width=True)
            
            # 提供下載
            with open(chart_path, "rb") as file:
                st.download_button(
                    label="📥 下載統一分析圖表",
                    data=file,
                    file_name="streamlit_unified_analysis.png",
                    mime="image/png"
                )
        
    except Exception as e:
        st.error(f"❌ 視覺化生成失敗: {e}")

def get_summary_stats():
    """獲取摘要統計"""
    try:
        with st.spinner("獲取統一摘要統計..."):
            engine = st.session_state.unified_engine
            stats = engine.get_summary_stats()
            st.session_state.summary_stats = stats
        
        display_summary_stats(stats)
        
    except Exception as e:
        st.error(f"❌ 摘要統計獲取失敗: {e}")

def create_main_content():
    """創建主要內容區域"""
    
    # 檢查資料載入狀態
    if not st.session_state.data_loaded:
        st.info("⚠️ 請先在側邊欄載入資料")
        
        # 顯示系統介紹
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 統一分析引擎特色")
            st.markdown("""
            - ✅ **一致性保證**: 與automated_pipeline使用相同核心
            - 🔧 **統一配置**: 相同的年齡分組和分析參數
            - 📊 **標準化輸出**: 統一的資料格式和視覺化
            - ⚡ **高效能**: 優化的分析演算法
            - 🔄 **同步更新**: 兩邊結果完全同步
            """)
        
        with col2:
            st.subheader("📋 分析模組")
            st.markdown("""
            1. **年齡偏好分析** - 各年齡層收視偏好
            2. **時段分析** - 不同時段年齡分布
            3. **性別差異分析** - 性別收視差異
            4. **週間vs週末分析** - 播出時間偏好
            5. **月份趨勢分析** - 季節性收視變化
            6. **統一視覺化** - 綜合分析圖表
            """)
        
        return
    
    # 創建分頁
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 整體概覽", "🎯 年齡偏好", "⏰ 時段分析", 
        "👥 性別差異", "📅 週間vs週末", "📈 趨勢分析"
    ])
    
    with tab1:
        show_overview_tab()
    
    with tab2:
        show_age_preferences_tab()
    
    with tab3:
        show_time_analysis_tab()
    
    with tab4:
        show_gender_analysis_tab()
    
    with tab5:
        show_weekday_weekend_tab()
    
    with tab6:
        show_trends_tab()

def show_overview_tab():
    """顯示整體概覽"""
    st.subheader("📊 統一分析系統概覽")
    
    # 摘要統計
    if hasattr(st.session_state, 'summary_stats'):
        display_summary_stats(st.session_state.summary_stats)
    elif st.button("🔄 獲取最新統計", key="overview_stats"):
        get_summary_stats()
    
    # 系統狀態
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **🔧 引擎狀態**
        - 核心引擎: ✅ 已載入
        - 視覺化引擎: ✅ 已載入  
        - 分析模式: 🎯 統一模式
        - 與automated_pipeline: ✅ 同步
        """)
    
    with col2:
        engine = st.session_state.unified_engine
        if engine.df is not None:
            st.success(f"""
            **📊 資料概況**
            - 資料筆數: {len(engine.df):,}
            - 劇集數量: {engine.df['Cleaned_Series_Name'].nunique()}
            - 年齡分組: {len(engine.config.age_groups)}
            - 時段分組: {len(engine.config.time_slots)}
            """)

def display_summary_stats(stats):
    """顯示摘要統計"""
    st.subheader("📈 關鍵統計指標")
    
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
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **📊 資料統計**
        - 總記錄數: {stats['total_records']:,}
        - 劇集總數: {stats['total_series']}
        - 性別差異: {stats['gender_difference']:.4f}
        """)
    
    with col2:
        start_date = stats['date_range'][0].strftime('%Y-%m-%d')
        end_date = stats['date_range'][1].strftime('%Y-%m-%d')
        st.info(f"""
        **📅 時間範圍**
        - 開始: {start_date}
        - 結束: {end_date}  
        - 最佳時段收視率: {stats['best_hour_rating']:.4f}
        """)

def show_age_preferences_tab():
    """顯示年齡偏好分析"""
    st.subheader("🎯 年齡偏好分析")
    
    if st.button("🔄 執行年齡偏好分析", key="age_pref_btn"):
        try:
            with st.spinner("分析中..."):
                engine = st.session_state.unified_engine
                result = engine.analyze_age_preferences(
                    st.session_state.min_episodes,
                    st.session_state.top_n_series
                )
                st.session_state.age_preferences = result
            
            st.success("✅ 年齡偏好分析完成")
        except Exception as e:
            st.error(f"❌ 分析失敗: {e}")
            return
    
    if hasattr(st.session_state, 'age_preferences') and not st.session_state.age_preferences.empty:
        result = st.session_state.age_preferences
        
        # 熱力圖
        st.subheader("📊 劇集年齡偏好熱力圖")
        pivot_data = result.pivot(index='Series', columns='Age_Group', values='Rating')
        
        fig = px.imshow(
            pivot_data.values,
            x=pivot_data.columns,
            y=pivot_data.index,
            color_continuous_scale='YlOrRd',
            aspect='auto',
            title="劇集年齡偏好分析（統一引擎版本）"
        )
        
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        # 詳細資料表
        st.subheader("📋 詳細資料")
        st.dataframe(pivot_data, use_container_width=True)
        
        # 統計摘要
        max_row = result.loc[result['Rating'].idxmax()]
        st.info(f"🏆 最高收視組合: {max_row['Series']} - {max_row['Age_Group']} ({max_row['Rating']:.4f})")

def show_time_analysis_tab():
    """顯示時段分析"""
    st.subheader("⏰ 時段年齡分布分析")
    
    if st.button("🔄 執行時段分析", key="time_analysis_btn"):
        try:
            with st.spinner("分析中..."):
                engine = st.session_state.unified_engine
                result = engine.analyze_time_demographics()
                st.session_state.time_demographics = result
            
            st.success("✅ 時段分析完成")
        except Exception as e:
            st.error(f"❌ 分析失敗: {e}")
            return
    
    if hasattr(st.session_state, 'time_demographics') and not st.session_state.time_demographics.empty:
        result = st.session_state.time_demographics
        
        # 長條圖
        fig = px.bar(
            result,
            x='Time_Slot',
            y='Rating',
            color='Age_Group',
            title="不同時段年齡分布（統一引擎版本）",
            barmode='group'
        )
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # 最佳時段統計
        st.subheader("🏆 各年齡層最佳時段")
        best_slots = result.loc[result.groupby('Age_Group')['Rating'].idxmax()]
        
        for _, row in best_slots.iterrows():
            st.metric(
                row['Age_Group'],
                row['Time_Slot'],
                f"{row['Rating']:.4f}"
            )

def show_gender_analysis_tab():
    """顯示性別差異分析"""
    st.subheader("👥 性別收視差異分析")
    
    if st.button("🔄 執行性別分析", key="gender_analysis_btn"):
        try:
            with st.spinner("分析中..."):
                engine = st.session_state.unified_engine
                overall, series = engine.analyze_gender_differences()
                st.session_state.gender_overall = overall
                st.session_state.gender_series = series
            
            st.success("✅ 性別分析完成")
        except Exception as e:
            st.error(f"❌ 分析失敗: {e}")
            return
    
    if (hasattr(st.session_state, 'gender_overall') and 
        not st.session_state.gender_overall.empty):
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 整體性別比較
            st.subheader("📊 整體性別收視比較")
            overall = st.session_state.gender_overall
            
            fig = px.bar(
                overall,
                x='Age_Group',
                y='Rating',
                color='Gender',
                title="各年齡層性別收視比較",
                barmode='group',
                color_discrete_map={'男性': 'lightblue', '女性': 'lightcoral'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 劇集性別偏好
            if (hasattr(st.session_state, 'gender_series') and 
                not st.session_state.gender_series.empty):
                
                st.subheader("🎭 劇集性別偏好")
                series = st.session_state.gender_series
                
                fig = px.bar(
                    series,
                    x='Rating',
                    y='Series',
                    color='Gender',
                    title="主要劇集性別偏好",
                    orientation='h',
                    color_discrete_map={'男性': 'lightblue', '女性': 'lightcoral'}
                )
                
                st.plotly_chart(fig, use_container_width=True)

def show_weekday_weekend_tab():
    """顯示週間vs週末分析"""
    st.subheader("📅 週間vs週末收視分析")
    
    if st.button("🔄 執行週間vs週末分析", key="weekday_analysis_btn"):
        try:
            with st.spinner("分析中..."):
                engine = st.session_state.unified_engine
                result = engine.analyze_weekday_weekend()
                st.session_state.weekday_weekend = result
            
            st.success("✅ 週間vs週末分析完成")
        except Exception as e:
            st.error(f"❌ 分析失敗: {e}")
            return
    
    if (hasattr(st.session_state, 'weekday_weekend') and 
        st.session_state.weekday_weekend):
        
        result = st.session_state.weekday_weekend
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 劇集表現
            if 'series' in result and not result['series'].empty:
                st.subheader("📺 劇集週間vs週末表現")
                
                fig = px.bar(
                    result['series'],
                    x='Series',
                    y='Rating',
                    color='Day_Type',
                    title="劇集週間vs週末表現",
                    barmode='group',
                    color_discrete_map={'週間': 'skyblue', '週末': 'orange'}
                )
                
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 年齡層偏好
            if 'age_groups' in result and not result['age_groups'].empty:
                st.subheader("👥 年齡層週間vs週末偏好")
                
                fig = px.bar(
                    result['age_groups'],
                    x='Age_Group',
                    y='Rating',
                    color='Day_Type',
                    title="年齡層週間vs週末偏好",
                    barmode='group',
                    color_discrete_map={'週間': 'skyblue', '週末': 'orange'}
                )
                
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

def show_trends_tab():
    """顯示趨勢分析"""
    st.subheader("📈 月份趨勢分析")
    
    if st.button("🔄 執行趨勢分析", key="trends_analysis_btn"):
        try:
            with st.spinner("分析中..."):
                engine = st.session_state.unified_engine
                result = engine.analyze_monthly_trends()
                st.session_state.monthly_trends = result
            
            st.success("✅ 趨勢分析完成")
        except Exception as e:
            st.error(f"❌ 分析失敗: {e}")
            return
    
    if (hasattr(st.session_state, 'monthly_trends') and 
        not st.session_state.monthly_trends.empty):
        
        result = st.session_state.monthly_trends
        
        # 線圖
        fig = go.Figure()
        
        main_groups = ['4歲以上', '15-44歲', '15-24歲', '55歲以上']
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        
        for i, group in enumerate(main_groups):
            group_data = result[result['Age_Group'] == group]
            if not group_data.empty:
                fig.add_trace(go.Scatter(
                    x=group_data['Month'],
                    y=group_data['Rating'],
                    mode='lines+markers',
                    name=group,
                    line=dict(color=colors[i], width=3)
                ))
        
        fig.update_layout(
            title="月份年齡趨勢（統一引擎版本）",
            xaxis_title="月份",
            yaxis_title="平均收視率",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 最佳/最差月份統計
        st.subheader("📊 月份統計摘要")
        
        for group in main_groups:
            group_data = result[result['Age_Group'] == group]
            if not group_data.empty:
                best_month = group_data.loc[group_data['Rating'].idxmax()]
                worst_month = group_data.loc[group_data['Rating'].idxmin()]
                
                st.write(f"**{group}**: "
                        f"最佳 {best_month['Month']}月 ({best_month['Rating']:.4f}), "
                        f"最差 {worst_month['Month']}月 ({worst_month['Rating']:.4f})")

if __name__ == "__main__":
    main()
