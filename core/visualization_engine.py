"""
visualization_engine.py

統一的視覺化引擎
為 Streamlit 和 automatic pipeline 提供一致的圖表生成
"""

import matplotlib
matplotlib.use('Agg')  # 使用非互動後端，避免GUI問題

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
import logging
import warnings
import os

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

class VisualizationEngine:
    """統一的視覺化引擎"""
    
    def __init__(self):
        self.setup_font()
        self.setup_style()
        logger.info("視覺化引擎初始化完成")
    
    def setup_font(self):
        """設定中文字體"""
        try:
            # 清除字體快取
            plt.rcParams.update(plt.rcParamsDefault)
            
            # 設定字體優先順序
            plt.rcParams['font.family'] = 'sans-serif'
            plt.rcParams['font.sans-serif'] = [
                'Heiti TC', 'STHeiti', 'SimHei', 
                'Microsoft JhengHei', 'Arial Unicode MS', 
                'DejaVu Sans'
            ]
            plt.rcParams['axes.unicode_minus'] = False
            plt.rcParams['font.size'] = 10
            
            logger.info("中文字體設定完成")
            
        except Exception as e:
            logger.warning(f"字體設定失敗，使用預設字體: {e}")
    
    def setup_style(self):
        """設定視覺化樣式"""
        sns.set_style("whitegrid")
        plt.style.use('default')
        
        # 設定色彩
        self.colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e', 
            'success': '#2ca02c',
            'danger': '#d62728',
            'warning': '#ff7f0e',
            'info': '#17becf',
            'light': '#7f7f7f',
            'dark': '#2f2f2f'
        }
        
        # 年齡層色彩映射
        self.age_colors = {
            '4歲以上': '#1f77b4',
            '15-44歲': '#ff7f0e',
            '15-24歲': '#2ca02c',
            '25-34歲': '#d62728',
            '35-44歲': '#9467bd',
            '45-54歲': '#8c564b',
            '55歲以上': '#e377c2'
        }
        
        # 性別色彩
        self.gender_colors = {
            '男性': 'lightblue',
            '女性': 'lightcoral'
        }
        
        # 週間/週末色彩
        self.day_colors = {
            '週間': 'skyblue',
            '週末': 'orange'
        }
        
        logger.info("視覺化樣式設定完成")
    
    def create_age_preference_heatmap(self, data: pd.DataFrame, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """創建年齡偏好熱力圖"""
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        
        try:
            # 轉換為樞紐表
            pivot_data = data.pivot(index='Series', columns='Age_Group', values='Rating')
            
            # 創建熱力圖
            sns.heatmap(
                pivot_data, 
                annot=True, 
                fmt='.3f', 
                cmap='YlOrRd',
                ax=ax,
                cbar_kws={'label': '收視率'}
            )
            
            ax.set_title('劇集年齡偏好分析', fontsize=12, pad=20)
            ax.set_xlabel('年齡群組', fontsize=10)
            ax.set_ylabel('劇集', fontsize=10)
            
            # 旋轉標籤
            ax.tick_params(axis='x', rotation=45, labelsize=9)
            ax.tick_params(axis='y', rotation=0, labelsize=9)
            
            logger.info("年齡偏好熱力圖創建完成")
            return ax
            
        except Exception as e:
            logger.error(f"創建年齡偏好熱力圖失敗: {e}")
            ax.text(0.5, 0.5, '資料載入失敗', ha='center', va='center', transform=ax.transAxes)
            return ax
    
    def create_time_demographics_chart(self, data: pd.DataFrame, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """創建時段年齡分布圖"""
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        
        try:
            # 轉換為樞紐表
            pivot_data = data.pivot(index='Time_Slot', columns='Age_Group', values='Rating')
            
            # 創建分群長條圖
            pivot_data.plot(
                kind='bar', 
                ax=ax, 
                width=0.8,
                color=[self.age_colors.get(col, self.colors['primary']) for col in pivot_data.columns]
            )
            
            ax.set_title('不同時段年齡分布', fontsize=12, pad=20)
            ax.set_xlabel('時段', fontsize=10)
            ax.set_ylabel('平均收視率', fontsize=10)
            
            # 設定圖例
            ax.legend(
                bbox_to_anchor=(1.05, 1), 
                loc='upper left', 
                fontsize=8
            )
            
            # 設定x軸標籤
            ax.tick_params(axis='x', rotation=0, labelsize=9)
            ax.tick_params(axis='y', labelsize=9)
            
            logger.info("時段年齡分布圖創建完成")
            return ax
            
        except Exception as e:
            logger.error(f"創建時段年齡分布圖失敗: {e}")
            ax.text(0.5, 0.5, '資料載入失敗', ha='center', va='center', transform=ax.transAxes)
            return ax
    
    def create_gender_comparison_chart(self, data: pd.DataFrame, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """創建性別差異比較圖"""
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        
        try:
            # 轉換為樞紐表
            pivot_data = data.pivot(index='Age_Group', columns='Gender', values='Rating')
            
            # 創建分群長條圖
            pivot_data.plot(
                kind='bar', 
                ax=ax,
                color=[self.gender_colors['男性'], self.gender_colors['女性']]
            )
            
            ax.set_title('各年齡層性別差異', fontsize=12, pad=20)
            ax.set_xlabel('年齡群組', fontsize=10)
            ax.set_ylabel('平均收視率', fontsize=10)
            
            # 設定圖例
            ax.legend(['男性', '女性'], fontsize=9)
            
            # 旋轉x軸標籤
            ax.tick_params(axis='x', rotation=45, labelsize=9)
            ax.tick_params(axis='y', labelsize=9)
            
            logger.info("性別差異比較圖創建完成")
            return ax
            
        except Exception as e:
            logger.error(f"創建性別差異比較圖失敗: {e}")
            ax.text(0.5, 0.5, '資料載入失敗', ha='center', va='center', transform=ax.transAxes)
            return ax
    
    def create_weekday_weekend_chart(self, data: pd.DataFrame, chart_type: str = 'series', 
                                   ax: Optional[plt.Axes] = None) -> plt.Axes:
        """創建週間vs週末圖表"""
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        
        try:
            if chart_type == 'series':
                # 劇集週間vs週末
                pivot_data = data.pivot(index='Series', columns='Day_Type', values='Rating')
                title = '劇集週間vs週末表現'
                xlabel = '劇集'
                rotation = 45
            else:
                # 年齡層週間vs週末  
                pivot_data = data.pivot(index='Age_Group', columns='Day_Type', values='Rating')
                title = '年齡層週間vs週末偏好'
                xlabel = '年齡群組'
                rotation = 45
            
            # 創建分群長條圖
            pivot_data.plot(
                kind='bar', 
                ax=ax,
                color=[self.day_colors['週間'], self.day_colors['週末']]
            )
            
            ax.set_title(title, fontsize=12, pad=20)
            ax.set_xlabel(xlabel, fontsize=10)
            ax.set_ylabel('平均收視率', fontsize=10)
            
            # 設定圖例
            ax.legend(['週間', '週末'], fontsize=9)
            
            # 設定x軸標籤旋轉
            ax.tick_params(axis='x', rotation=rotation, labelsize=9)
            ax.tick_params(axis='y', labelsize=9)
            
            logger.info(f"{title}創建完成")
            return ax
            
        except Exception as e:
            logger.error(f"創建週間vs週末圖表失敗: {e}")
            ax.text(0.5, 0.5, '資料載入失敗', ha='center', va='center', transform=ax.transAxes)
            return ax
    
    def create_monthly_trends_chart(self, data: pd.DataFrame, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """創建月份趨勢圖"""
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        
        try:
            # 選取主要年齡層
            main_groups = ['4歲以上', '15-44歲', '15-24歲', '55歲以上']
            
            for i, group in enumerate(main_groups):
                group_data = data[data['Age_Group'] == group]
                if not group_data.empty:
                    ax.plot(
                        group_data['Month'], 
                        group_data['Rating'], 
                        marker='o', 
                        label=group, 
                        linewidth=2,
                        color=self.age_colors.get(group, self.colors['primary'])
                    )
            
            ax.set_title('月份年齡趨勢', fontsize=12, pad=20)
            ax.set_xlabel('月份', fontsize=10)
            ax.set_ylabel('平均收視率', fontsize=10)
            
            # 設定圖例
            ax.legend(fontsize=9)
            
            # 設定x軸刻度
            ax.set_xticks(range(1, 13))
            ax.tick_params(labelsize=9)
            
            # 添加網格
            ax.grid(True, alpha=0.3)
            
            logger.info("月份趨勢圖創建完成")
            return ax
            
        except Exception as e:
            logger.error(f"創建月份趨勢圖失敗: {e}")
            ax.text(0.5, 0.5, '資料載入失敗', ha='center', va='center', transform=ax.transAxes)
            return ax
    
    def create_age_distribution_pie(self, summary_stats: Dict, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """創建年齡分布餅圖"""
        if ax is None:
            fig, ax = plt.subplots(figsize=(8, 8))
        
        try:
            # 模擬年齡分布資料（實際應從資料中計算）
            age_distribution = {
                '15-24歲': 0.15,
                '25-34歲': 0.25,
                '35-44歲': 0.22,
                '45-54歲': 0.20,
                '55歲以上': 0.18
            }
            
            colors = [self.age_colors.get(age, self.colors['primary']) for age in age_distribution.keys()]
            
            wedges, texts, autotexts = ax.pie(
                age_distribution.values(),
                labels=age_distribution.keys(),
                autopct='%1.1f%%',
                startangle=90,
                colors=colors,
                textprops={'fontsize': 9}
            )
            
            ax.set_title('整體年齡分布占比', fontsize=12, pad=20)
            
            logger.info("年齡分布餅圖創建完成")
            return ax
            
        except Exception as e:
            logger.error(f"創建年齡分布餅圖失敗: {e}")
            ax.text(0.5, 0.5, '資料載入失敗', ha='center', va='center', transform=ax.transAxes)
            return ax
    
    def create_series_gender_preference_chart(self, data: pd.DataFrame, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """創建劇集性別偏好圖"""
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        
        try:
            # 轉換為樞紐表
            pivot_data = data.pivot(index='Series', columns='Gender', values='Rating')
            
            # 創建水平長條圖
            pivot_data.plot(
                kind='barh', 
                ax=ax,
                color=[self.gender_colors['男性'], self.gender_colors['女性']]
            )
            
            ax.set_title('主要劇集性別偏好', fontsize=12, pad=20)
            ax.set_xlabel('平均收視率', fontsize=10)
            ax.set_ylabel('劇集', fontsize=10)
            
            # 設定圖例
            ax.legend(['男性', '女性'], fontsize=9)
            
            # 設定標籤大小
            ax.tick_params(labelsize=9)
            
            logger.info("劇集性別偏好圖創建完成")
            return ax
            
        except Exception as e:
            logger.error(f"創建劇集性別偏好圖失敗: {e}")
            ax.text(0.5, 0.5, '資料載入失敗', ha='center', va='center', transform=ax.transAxes)
            return ax
    
    def create_comprehensive_dashboard(self, analysis_results: Dict, 
                                     save_path: str = 'unified_drama_age_analysis.png') -> str:
        """創建綜合分析儀表板"""
        logger.info("開始創建綜合分析儀表板")
        
        try:
            # 創建3x3子圖
            fig, axes = plt.subplots(3, 3, figsize=(18, 15))
            fig.suptitle('愛爾達綜合台年齡分層收視分析（統一版本）', 
                        fontsize=16, fontweight='bold', y=0.98)
            
            # 1. 年齡偏好熱力圖
            if 'age_preferences' in analysis_results and not analysis_results['age_preferences'].empty:
                self.create_age_preference_heatmap(analysis_results['age_preferences'], axes[0, 0])
            
            # 2. 時段年齡分布
            if 'time_demographics' in analysis_results and not analysis_results['time_demographics'].empty:
                self.create_time_demographics_chart(analysis_results['time_demographics'], axes[0, 1])
            
            # 3. 性別差異
            if 'gender_overall' in analysis_results and not analysis_results['gender_overall'].empty:
                self.create_gender_comparison_chart(analysis_results['gender_overall'], axes[0, 2])
            
            # 4. 劇集週間vs週末
            if ('weekday_weekend' in analysis_results and 
                'series' in analysis_results['weekday_weekend'] and 
                not analysis_results['weekday_weekend']['series'].empty):
                self.create_weekday_weekend_chart(
                    analysis_results['weekday_weekend']['series'], 
                    'series', 
                    axes[1, 0]
                )
            
            # 5. 年齡層週間vs週末
            if ('weekday_weekend' in analysis_results and 
                'age_groups' in analysis_results['weekday_weekend'] and 
                not analysis_results['weekday_weekend']['age_groups'].empty):
                self.create_weekday_weekend_chart(
                    analysis_results['weekday_weekend']['age_groups'], 
                    'age_groups', 
                    axes[1, 1]
                )
            
            # 6. 月份趨勢
            if 'monthly_trends' in analysis_results and not analysis_results['monthly_trends'].empty:
                self.create_monthly_trends_chart(analysis_results['monthly_trends'], axes[1, 2])
            
            # 7. 劇集性別偏好
            if 'gender_series' in analysis_results and not analysis_results['gender_series'].empty:
                self.create_series_gender_preference_chart(analysis_results['gender_series'], axes[2, 0])
            
            # 8. 年齡分布餅圖
            if 'summary_stats' in analysis_results:
                self.create_age_distribution_pie(analysis_results['summary_stats'], axes[2, 1])
            
            # 9. 綜合統計資訊
            if 'summary_stats' in analysis_results:
                stats = analysis_results['summary_stats']
                axes[2, 2].axis('off')
                
                stats_text = f"""
📊 分析摘要

• 主要觀眾群: {stats.get('main_audience', 'N/A')}
• 平均收視率: {stats.get('main_audience_rating', 0):.4f}
• 性別偏向: {stats.get('gender_bias', 'N/A')}
• 最佳時段: {stats.get('best_hour', 'N/A')}點
• 總資料筆數: {stats.get('total_records', 0):,}
• 劇集總數: {stats.get('total_series', 0)}
                """
                
                axes[2, 2].text(0.1, 0.9, stats_text, transform=axes[2, 2].transAxes,
                               fontsize=11, verticalalignment='top',
                               bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.5))
            
            # 調整佈局
            plt.tight_layout()
            
            # 儲存圖表
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"綜合分析儀表板已儲存至: {save_path}")
            
            # 顯示圖表（如果在互動環境中）
            try:
                # 在自動化環境中不顯示圖表
                if os.environ.get('DISPLAY') and not os.environ.get('AUTOMATED_MODE'):
                    plt.show()
            except:
                # 靜默忽略顯示錯誤
                pass
            
            return save_path
            
        except Exception as e:
            error_msg = f"創建綜合分析儀表板失敗: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def create_streamlit_compatible_charts(self, analysis_results: Dict) -> Dict[str, plt.Figure]:
        """為Streamlit創建兼容的圖表"""
        logger.info("創建Streamlit兼容圖表")
        
        charts = {}
        
        try:
            # 1. 年齡偏好熱力圖
            if 'age_preferences' in analysis_results and not analysis_results['age_preferences'].empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                self.create_age_preference_heatmap(analysis_results['age_preferences'], ax)
                charts['age_preferences'] = fig
            
            # 2. 時段分析
            if 'time_demographics' in analysis_results and not analysis_results['time_demographics'].empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                self.create_time_demographics_chart(analysis_results['time_demographics'], ax)
                charts['time_demographics'] = fig
            
            # 3. 性別差異
            if 'gender_overall' in analysis_results and not analysis_results['gender_overall'].empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                self.create_gender_comparison_chart(analysis_results['gender_overall'], ax)
                charts['gender_overall'] = fig
            
            # 4. 週間vs週末（劇集）
            if ('weekday_weekend' in analysis_results and 
                'series' in analysis_results['weekday_weekend'] and 
                not analysis_results['weekday_weekend']['series'].empty):
                fig, ax = plt.subplots(figsize=(12, 6))
                self.create_weekday_weekend_chart(
                    analysis_results['weekday_weekend']['series'], 
                    'series', 
                    ax
                )
                charts['weekday_weekend_series'] = fig
            
            # 5. 週間vs週末（年齡層）
            if ('weekday_weekend' in analysis_results and 
                'age_groups' in analysis_results['weekday_weekend'] and 
                not analysis_results['weekday_weekend']['age_groups'].empty):
                fig, ax = plt.subplots(figsize=(10, 6))
                self.create_weekday_weekend_chart(
                    analysis_results['weekday_weekend']['age_groups'], 
                    'age_groups', 
                    ax
                )
                charts['weekday_weekend_age'] = fig
            
            logger.info(f"已創建 {len(charts)} 個Streamlit兼容圖表")
            return charts
            
        except Exception as e:
            logger.error(f"創建Streamlit兼容圖表失敗: {e}")
            return {}
