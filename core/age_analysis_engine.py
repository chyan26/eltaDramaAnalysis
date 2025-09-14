"""
age_analysis_engine.py

統一的年齡分析引擎
供 Streamlit 管理中心和 automatic pipeline 共用
確保兩邊使用相同的分析邏輯，避免結果不一致
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AgeAnalysisConfig:
    """年齡分析配置類"""
    age_groups: Dict[str, List[str]]
    gender_groups: Dict[str, str]
    time_slots: Dict[str, Tuple[int, int]]
    
    @classmethod
    def default(cls):
        return cls(
            age_groups={
                '4歲以上': ['4歲以上'],
                '15-44歲': ['15-44歲'],
                '15-24歲': ['15-24歲'],
                '25-34歲': ['25-34歲'],
                '35-44歲': ['35-44歲'],
                '45-54歲': ['45-54歲'],
                '55歲以上': ['55歲以上']
            },
            gender_groups={
                '4歲以上男性': '4歲以上男性',
                '4歲以上女性': '4歲以上女性',
                '15-24歲男性': '15-24歲男性',
                '15-24歲女性': '15-24歲女性',
                '25-34歲男性': '25-34歲男性',
                '25-34歲女性': '25-34歲女性',
                '35-44歲男性': '35-44歲男性',
                '35-44歲女性': '35-44歲女性',
                '45-54歲男性': '45-54歲男性',
                '45-54歲女性': '45-54歲女性',
                '55歲以上男性': '55歲以上男性',
                '55歲以上女性': '55歲以上女性'
            },
            time_slots={
                '凌晨': (0, 5),
                '早晨': (6, 11),
                '午間': (12, 17),
                '黃金': (18, 22),
                '深夜': (23, 23)
            }
        )

class AgeAnalysisEngine:
    """統一的年齡分析引擎"""
    
    def __init__(self, config: Optional[AgeAnalysisConfig] = None):
        self.config = config or AgeAnalysisConfig.default()
        self.df = None
        logger.info("年齡分析引擎初始化完成")
        
    def load_data(self, file_path: str = 'ACNelson_normalized_with_age.csv') -> pd.DataFrame:
        """載入並預處理資料"""
        try:
            logger.info(f"正在載入資料: {file_path}")
            self.df = pd.read_csv(file_path)
            
            # 資料預處理
            self.df['Date'] = pd.to_datetime(self.df['Date'])
            self.df['Hour'] = pd.to_datetime(self.df['Time'], format='%H:%M:%S').dt.hour
            self.df['Month'] = self.df['Date'].dt.month
            self.df['Weekday_Num'] = self.df['Date'].dt.dayofweek
            self.df['Is_Weekend'] = self.df['Weekday_Num'].isin([5, 6])
            
            # 過濾無效資料
            self.df = self.df[self.df['Rating'] > 0]
            
            logger.info(f"資料載入成功: {len(self.df):,} 筆有效資料")
            logger.info(f"時間範圍: {self.df['Date'].min().date()} 至 {self.df['Date'].max().date()}")
            logger.info(f"包含劇集: {self.df['Cleaned_Series_Name'].nunique()} 部")
            
            return self.df
            
        except FileNotFoundError:
            error_msg = f"找不到資料檔案: {file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        except Exception as e:
            error_msg = f"載入資料時發生錯誤: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def analyze_age_preferences(self, min_episodes: int = 50, top_n: int = 10) -> pd.DataFrame:
        """分析年齡偏好，返回標準化資料"""
        if self.df is None:
            raise ValueError("請先載入資料")
            
        logger.info(f"開始分析年齡偏好 (最少{min_episodes}集, 前{top_n}部劇)")
        
        # 找出主要劇集
        series_counts = self.df['Cleaned_Series_Name'].value_counts()
        major_series = series_counts[series_counts >= min_episodes].head(top_n)
        
        logger.info(f"找到符合條件的劇集: {len(major_series)} 部")
        
        results = []
        for series_name in major_series.index:
            series_data = self.df[self.df['Cleaned_Series_Name'] == series_name]
            
            # 計算各年齡層收視率
            for group_name, columns in self.config.age_groups.items():
                if columns[0] in series_data.columns:
                    avg_rating = series_data[columns[0]].mean()
                    results.append({
                        'Series': series_name,
                        'Age_Group': group_name,
                        'Rating': avg_rating,
                        'Episodes': len(series_data)
                    })
        
        result_df = pd.DataFrame(results)
        logger.info(f"年齡偏好分析完成: {len(result_df)} 筆分析結果")
        return result_df
    
    def analyze_time_demographics(self) -> pd.DataFrame:
        """分析時段人口統計"""
        if self.df is None:
            raise ValueError("請先載入資料")
            
        logger.info("開始分析時段人口統計")
        
        results = []
        for slot_name, (start_hour, end_hour) in self.config.time_slots.items():
            slot_data = self.df[self.df['Hour'].between(start_hour, end_hour)]
            
            if len(slot_data) > 0:
                for group_name, columns in self.config.age_groups.items():
                    if columns[0] in slot_data.columns:
                        avg_rating = slot_data[columns[0]].mean()
                        results.append({
                            'Time_Slot': slot_name,
                            'Age_Group': group_name,
                            'Rating': avg_rating,
                            'Data_Points': len(slot_data)
                        })
        
        result_df = pd.DataFrame(results)
        logger.info(f"時段分析完成: {len(result_df)} 筆分析結果")
        return result_df
    
    def analyze_gender_differences(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """分析性別差異"""
        if self.df is None:
            raise ValueError("請先載入資料")
            
        logger.info("開始分析性別差異")
        
        # 整體性別分析
        overall_results = []
        age_gender_pairs = [
            ('15-24歲', '15-24歲男性', '15-24歲女性'),
            ('25-34歲', '25-34歲男性', '25-34歲女性'),
            ('35-44歲', '35-44歲男性', '35-44歲女性'),
            ('45-54歲', '45-54歲男性', '45-54歲女性'),
            ('55歲以上', '55歲以上男性', '55歲以上女性')
        ]
        
        for age_group, male_col, female_col in age_gender_pairs:
            if male_col in self.df.columns and female_col in self.df.columns:
                male_avg = self.df[male_col].mean()
                female_avg = self.df[female_col].mean()
                
                overall_results.extend([
                    {'Age_Group': age_group, 'Gender': '男性', 'Rating': male_avg},
                    {'Age_Group': age_group, 'Gender': '女性', 'Rating': female_avg}
                ])
        
        # 劇集性別分析
        series_counts = self.df['Cleaned_Series_Name'].value_counts()
        major_series = series_counts[series_counts >= 50].head(8)
        
        series_results = []
        for series_name in major_series.index:
            series_data = self.df[self.df['Cleaned_Series_Name'] == series_name]
            
            if '4歲以上男性' in series_data.columns and '4歲以上女性' in series_data.columns:
                male_rating = series_data['4歲以上男性'].mean()
                female_rating = series_data['4歲以上女性'].mean()
                
                series_results.extend([
                    {'Series': series_name, 'Gender': '男性', 'Rating': male_rating},
                    {'Series': series_name, 'Gender': '女性', 'Rating': female_rating}
                ])
        
        overall_df = pd.DataFrame(overall_results)
        series_df = pd.DataFrame(series_results)
        
        logger.info(f"性別差異分析完成: 整體{len(overall_df)}筆, 劇集{len(series_df)}筆")
        return overall_df, series_df
    
    def analyze_weekday_weekend(self) -> Dict[str, pd.DataFrame]:
        """分析週間vs週末表現"""
        if self.df is None:
            raise ValueError("請先載入資料")
            
        logger.info("開始分析週間vs週末表現")
        
        weekday_data = self.df[~self.df['Is_Weekend']]
        weekend_data = self.df[self.df['Is_Weekend']]
        
        # 劇集表現分析
        series_results = []
        series_counts = self.df['Cleaned_Series_Name'].value_counts()
        major_series = series_counts[series_counts >= 30].head(12)
        
        for series_name in major_series.index:
            series_data = self.df[self.df['Cleaned_Series_Name'] == series_name]
            series_weekday = series_data[~series_data['Is_Weekend']]
            series_weekend = series_data[series_data['Is_Weekend']]
            
            if len(series_weekday) > 0 and len(series_weekend) > 0:
                weekday_rating = series_weekday['4歲以上'].mean()
                weekend_rating = series_weekend['4歲以上'].mean()
                
                series_results.extend([
                    {'Series': series_name, 'Day_Type': '週間', 'Rating': weekday_rating},
                    {'Series': series_name, 'Day_Type': '週末', 'Rating': weekend_rating}
                ])
        
        # 年齡層分析
        age_results = []
        for group_name, columns in self.config.age_groups.items():
            if columns[0] in self.df.columns:
                weekday_age = weekday_data[columns[0]].mean()
                weekend_age = weekend_data[columns[0]].mean()
                
                age_results.extend([
                    {'Age_Group': group_name, 'Day_Type': '週間', 'Rating': weekday_age},
                    {'Age_Group': group_name, 'Day_Type': '週末', 'Rating': weekend_age}
                ])
        
        series_df = pd.DataFrame(series_results)
        age_df = pd.DataFrame(age_results)
        
        logger.info(f"週間vs週末分析完成: 劇集{len(series_df)}筆, 年齡層{len(age_df)}筆")
        
        return {
            'series': series_df,
            'age_groups': age_df
        }
    
    def analyze_monthly_trends(self) -> pd.DataFrame:
        """分析月份趨勢"""
        if self.df is None:
            raise ValueError("請先載入資料")
            
        logger.info("開始分析月份趨勢")
        
        results = []
        for month in range(1, 13):
            month_data = self.df[self.df['Month'] == month]
            
            if len(month_data) > 0:
                for group_name, columns in self.config.age_groups.items():
                    if columns[0] in month_data.columns:
                        avg_rating = month_data[columns[0]].mean()
                        results.append({
                            'Month': month,
                            'Age_Group': group_name,
                            'Rating': avg_rating,
                            'Data_Points': len(month_data)
                        })
        
        result_df = pd.DataFrame(results)
        logger.info(f"月份趨勢分析完成: {len(result_df)} 筆分析結果")
        return result_df
    
    def get_summary_stats(self) -> Dict:
        """獲取摘要統計"""
        if self.df is None:
            raise ValueError("請先載入資料")
            
        logger.info("生成摘要統計")
        
        # 主要觀眾群
        age_ratings = {}
        for group_name, columns in self.config.age_groups.items():
            if columns[0] in self.df.columns:
                age_ratings[group_name] = self.df[columns[0]].mean()
        
        main_audience = max(age_ratings, key=age_ratings.get)
        
        # 性別差異
        male_avg = self.df['4歲以上男性'].mean() if '4歲以上男性' in self.df.columns else 0
        female_avg = self.df['4歲以上女性'].mean() if '4歲以上女性' in self.df.columns else 0
        
        # 最佳時段
        hourly_ratings = self.df.groupby('Hour')['4歲以上'].mean()
        best_hour = hourly_ratings.idxmax()
        
        stats = {
            'main_audience': main_audience,
            'main_audience_rating': age_ratings[main_audience],
            'gender_bias': '女性' if female_avg > male_avg else '男性',
            'gender_difference': abs(male_avg - female_avg),
            'best_hour': best_hour,
            'best_hour_rating': hourly_ratings[best_hour],
            'total_records': len(self.df),
            'total_series': self.df['Cleaned_Series_Name'].nunique(),
            'date_range': (self.df['Date'].min(), self.df['Date'].max())
        }
        
        logger.info("摘要統計生成完成")
        return stats
    
    def run_complete_analysis(self, min_episodes: int = 50, top_n: int = 10) -> Dict:
        """執行完整分析並返回所有結果"""
        logger.info("開始執行完整年齡分層分析")
        
        if self.df is None:
            self.load_data()
        
        results = {}
        
        try:
            # 1. 年齡偏好分析
            results['age_preferences'] = self.analyze_age_preferences(min_episodes, top_n)
            
            # 2. 時段分析
            results['time_demographics'] = self.analyze_time_demographics()
            
            # 3. 性別差異分析
            overall_gender, series_gender = self.analyze_gender_differences()
            results['gender_overall'] = overall_gender
            results['gender_series'] = series_gender
            
            # 4. 週間vs週末分析
            weekday_weekend = self.analyze_weekday_weekend()
            results['weekday_weekend'] = weekday_weekend
            
            # 5. 月份趨勢分析
            results['monthly_trends'] = self.analyze_monthly_trends()
            
            # 6. 摘要統計
            results['summary_stats'] = self.get_summary_stats()
            
            logger.info("完整年齡分層分析執行完成")
            return results
            
        except Exception as e:
            error_msg = f"執行完整分析時發生錯誤: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def export_results(self, results: Dict, output_dir: str = 'outputs') -> Dict[str, str]:
        """導出分析結果到檔案"""
        import os
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        exported_files = {}
        
        try:
            # 導出各項分析結果
            for key, data in results.items():
                if isinstance(data, pd.DataFrame) and not data.empty:
                    filename = f"{key}_analysis.csv"
                    filepath = os.path.join(output_dir, filename)
                    data.to_csv(filepath, index=False, encoding='utf-8-sig')
                    exported_files[key] = filepath
                    logger.info(f"已導出: {filepath}")
                elif key == 'summary_stats':
                    # 導出摘要統計為JSON
                    import json
                    filename = "summary_stats.json"
                    filepath = os.path.join(output_dir, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        # 處理datetime對象和numpy數據類型
                        stats_copy = {}
                        for k, v in data.items():
                            if hasattr(v, 'isoformat'):  # datetime對象
                                stats_copy[k] = v.isoformat()
                            elif hasattr(v, 'item'):  # numpy數據類型
                                stats_copy[k] = v.item()
                            elif isinstance(v, (list, tuple)) and len(v) > 0:
                                # 處理datetime列表
                                if hasattr(v[0], 'isoformat'):
                                    stats_copy[k] = [dt.isoformat() for dt in v]
                                else:
                                    stats_copy[k] = [x.item() if hasattr(x, 'item') else x for x in v]
                            else:
                                stats_copy[k] = v
                                
                        json.dump(stats_copy, f, ensure_ascii=False, indent=2)
                    exported_files[key] = filepath
                    logger.info(f"已導出: {filepath}")
            
            logger.info(f"結果導出完成，共 {len(exported_files)} 個檔案")
            return exported_files
            
        except Exception as e:
            error_msg = f"導出結果時發生錯誤: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
